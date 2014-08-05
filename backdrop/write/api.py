from os import getenv
import json

from flask import abort, Flask, g, jsonify, request
from flask_featureflags import FeatureFlag
from backdrop import statsd
from backdrop.core.data_set import DataSet
from backdrop.core.flaskutils import DataSetConverter
from backdrop.write.decompressing_request import DecompressingRequest

from ..core.errors import ParseError, ValidationError
from ..core import log_handler, cache_control

from ..core.storage.mongo import MongoStorageEngine

from .validation import auth_header_is_valid, extract_bearer_token

from performanceplatform import client


GOVUK_ENV = getenv("GOVUK_ENV", "development")

app = Flask("backdrop.write.api")

# We want to allow clients to compress large JSON documents.
app.request_class = DecompressingRequest

feature_flags = FeatureFlag(app)

# Configuration
app.config.from_object(
    "backdrop.write.config.{}".format(GOVUK_ENV))

storage = MongoStorageEngine.create(
    app.config['MONGO_HOSTS'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME'])

admin_api = client.AdminAPI(
    app.config['STAGECRAFT_URL'],
    app.config['SIGNON_API_USER_TOKEN'],
    dry_run=False,
)

log_handler.set_up_logging(app, GOVUK_ENV)

app.url_map.converters["data_set"] = DataSetConverter


def _record_write_error(e):
    app.logger.exception(e)

    name_or_path = getattr(g, 'data_set_name', request.path)

    statsd.incr("write.error", data_set=name_or_path)
    if getattr(e, 'code', None) == 401:
        statsd.incr("write_api.bad_token", data_set=name_or_path)


@app.errorhandler(500)
def uncaught_error_handler(e):
    """
    This shouldn't happen. If we get here an unspecified uncaught exception
    *or* an explicit 500 was raised.
    WARNING: Don't assume the exception will be a subclass of HTTPError:
    'a handler for internal server errors will be passed other exception
    instances as well if they are uncaught'
    -- http://flask.pocoo.org/docs/patterns/errorpages/#error-handlers
    """
    _record_write_error(e)

    error_message = 'Internal Server Error: {}'.format(repr(e))
    return (jsonify(status='error', message=error_message), 500)


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(405)
def http_error_handler(e):
    if e.code == 401:
        description = getattr(e, 'description',
                              'Bad or missing Authorization header')
        return (jsonify(status='error', message=description),
                401,
                [('WWW-Authenticate', 'bearer')])
    else:
        description = getattr(e, 'description', "Unknown Error")

        return (jsonify(status='error', message=description), e.code)


@app.route('/_status', methods=['GET'])
@cache_control.nocache
@statsd.timer('write.route.health_check.status')
def health_check():
    if storage.alive():
        return jsonify(status='ok', message='database seems fine')
    else:
        abort(500, 'cannot connect to database')


@app.route('/data/<data_group>/<data_type>', methods=['POST'])
@cache_control.nocache
def write_by_group(data_group, data_type):
    """
    Write by group/type
    e.g. POST https://BACKDROP/data/my-transaction-name/volumetrics
    """
    with statsd.timer('write.route.data.{data_group}.{data_type}'.format(
            data_group=data_group,
            data_type=data_type)):
        data_set_config = admin_api.get_data_set(data_group, data_type)

        _validate_config(data_set_config)
        _validate_auth(data_set_config)

        try:
            data = listify_json(get_json_from_request(request))
            return _append_to_data_set(data_set_config, data)

        except (ParseError, ValidationError) as e:
            abort(400, repr(e))


@app.route('/data/<data_group>/<data_type>', methods=['PUT'])
@cache_control.nocache
@statsd.timer('write.route.data.empty.data_set')
def put_by_group_and_type(data_group, data_type):
    """
    Put by group/type
    e.g. PUT https://BACKDROP/data/gcloud/sales
    Note: At the moment this is just being used to empty data-sets.
          Trying to PUT a non empty list of records will result in a
          PutNonEmptyNotImplementedError exception.
    """
    data_set_config = admin_api.get_data_set(data_group, data_type)

    _validate_config(data_set_config)
    _validate_auth(data_set_config)

    try:
        data = listify_json(get_json_from_request(request))
        if len(data) > 0:
            abort(400, 'Not implemented: you can only pass an empty JSON list')

        return _empty_data_set(data_set_config)

    except (ParseError, ValidationError) as e:
        abort(400, repr(e))


@app.route('/<data_set:data_set_name>', methods=['POST'])
@cache_control.nocache
def post_to_data_set(data_set_name):
    app.logger.warning("Deprecated use of write API by name: {}".format(
        data_set_name))
    data_set_config = admin_api.get_data_set_by_name(data_set_name)

    _validate_config(data_set_config)
    _validate_auth(data_set_config)

    try:
        data = listify_json(get_json_from_request(request))
        return _append_to_data_set(
            data_set_config,
            data,
            ok_message="Deprecation Warning: accessing by data-set name is "
                       "deprecated, Please use the /data-group/data-type form")

    except (ParseError, ValidationError) as e:
        abort(400, repr(e))


@app.route('/data-sets/<data_set_name>', methods=['DELETE'])
@cache_control.nocache
@statsd.timer('write.route.delete_data_set')
def delete_collection_by_data_set_name(data_set_name):
    if not _allow_create_collection(request.headers.get('Authorization')):
        abort(
            401, 'Unauthorized: invalid or no token given for "{}".'.format(
                data_set_name
            )
        )

    if not storage.data_set_exists(data_set_name):
        abort(404, 'No collection exists with name "{}"'.format(data_set_name))

    storage.delete_data_set(data_set_name)

    return jsonify(status='ok', message='Deleted {}'.format(data_set_name))


def _allow_modify_collection(auth_header):
    token = extract_bearer_token(auth_header)
    if token == app.config['STAGECRAFT_COLLECTION_ENDPOINT_TOKEN']:
        return True

    app.logger.info("Bad token for create collection: '{}'".format(token))
    return False


def _allow_delete_collection(auth_header):
    return _allow_modify_collection(auth_header)


def _allow_create_collection(auth_header):
    return _allow_modify_collection(auth_header)


def _validate_config(data_set_config):
    if data_set_config is None:
        abort(404, 'Could not find data_set_config')

    g.data_set_name = data_set_config['name']


def _validate_auth(data_set_config):
    try:
        auth_header = request.headers['Authorization']
    except KeyError:
        abort(401, 'Expected header of form: Authorization: Bearer <token>')

    if not auth_header_is_valid(data_set_config, auth_header):
        token = extract_bearer_token(auth_header)
        abort(401,
              'Unauthorized: Invalid bearer token \'{0}\' for \'{1}\''.format(
                  token, data_set_config['name']))


def _append_to_data_set(data_set_config, data, ok_message=None):
    data_set = DataSet(storage, data_set_config)
    data_set.create_if_not_exists()
    data_set.store(data)

    if ok_message:
        return jsonify(status='ok', message=ok_message)
    else:
        return jsonify(status='ok')


def _empty_data_set(data_set_config):
    data_set = DataSet(storage, data_set_config)
    data_set.create_if_not_exists()
    data_set.empty()
    return jsonify(
        status='ok',
        message='{} now contains 0 records'.format(data_set_config['name']))


def get_json_from_request(request):
    def json_error_handler(e):
        app.logger.exception(e)
        abort(400, 'Error parsing JSON: "{}"'.format(str(e)))

    if len(request.data) == 0:
        abort(400, 'Expected JSON request body but received zero bytes.')

    request.on_json_loading_failed = json_error_handler
    return request.get_json()


def listify_json(data):
    if data is None:
        raise ValidationError(
            "Expected header: Content-type: application/json")

    if isinstance(data, list):
        return data
    else:
        return [data]


def start(port):
    # this method only gets run on dev
    # app.debug = True
    app.run(host='0.0.0.0', port=port)
    app.logger.info("Backdrop Write API started")

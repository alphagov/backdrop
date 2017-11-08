import datetime
from os import getenv

import pytz
from celery import Celery
from dateutil.parser import parse as datetime_parse
from flask import abort, Flask, g, jsonify, request
from flask_featureflags import FeatureFlag
from performanceplatform import client

from backdrop import statsd
from backdrop.core.data_set import DataSet
from backdrop.core.flaskutils import DataSetConverter
from backdrop.write.decompressing_request import DecompressingRequest
from .validation import auth_header_is_valid, extract_bearer_token
from ..core import log_handler, cache_control
from ..core.errors import ParseError, ValidationError
from ..core.flaskutils import generate_request_id
from ..core.storage.mongo import MongoStorageEngine

ENVIRONMENT = getenv("ENVIRONMENT", "development")

app = Flask("backdrop.write.api")

# We want to allow clients to compress large JSON documents.
app.request_class = DecompressingRequest

feature_flags = FeatureFlag(app)

# Configuration
app.config.from_object(
    "backdrop.write.config.{}".format(ENVIRONMENT))

storage = MongoStorageEngine.create(
    app.config['DATABASE_URL'],
    app.config.get('CA_CERTIFICATE')
)

admin_api = client.AdminAPI(
    app.config['STAGECRAFT_URL'],
    app.config['SIGNON_API_USER_TOKEN'],
    dry_run=False,
    request_id_fn=generate_request_id,
)

log_handler.set_up_logging(app, ENVIRONMENT)
log_handler.set_up_audit_logging(app, ENVIRONMENT)

app.url_map.converters["data_set"] = DataSetConverter

celery_app = Celery(broker=app.config['TRANSFORMER_AMQP_URL'])
app.config['BROKER_FAILOVER_STRATEGY'] = "round-robin"
celery_app.conf.update(app.config)


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
    if e.code in [401, 403]:
        name_or_path = getattr(g, 'data_set_name', request.path)
        app.audit_logger.info("Bad auth", extra={'data_set': name_or_path})

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
    return jsonify(status='ok', message='app is up')


@app.route('/data/<data_group>/<data_type>', methods=['POST'])
@cache_control.nocache
def write_by_group(data_group, data_type):
    """
    Write by group/type
    e.g. POST https://BACKDROP/data/my-transaction-name/volumetrics
    """
    data_set_config = admin_api.get_data_set(data_group, data_type)

    _validate_config(data_set_config)
    _validate_auth(data_set_config)

    try:
        data = listify_json(get_json_from_request(request))
    except ValidationError as e:
        return (jsonify(messages=[repr(e)]), 400)
    errors = _append_to_data_set(data_set_config, data)

    if errors:
        return (jsonify(messages=errors), 400)
    else:
        trigger_transforms(data_set_config, data)
        return jsonify(status='ok')


@app.route('/data/<data_group>/<data_type>/<data_set_id>', methods=['DELETE'])
@cache_control.nocache
@statsd.timer('write.route.data.delete.data_set')
def delete_by_group_type_and_id(data_group, data_type, data_set_id):
    """
    Delete by group, type and id
    e.g. DELETE https://BACKDROP/data/gcloud/sales/MjAxNi0wOC0xNSAwMDowMD
    """

    data_set_config = admin_api.get_data_set(data_group, data_type)
    _validate_config(data_set_config)
    _validate_auth(data_set_config)

    try:
        errors = _delete_data_set(data_set_config, data_set_id)
        if errors:
            return (jsonify(messages=errors), 400)
        return jsonify(status='ok')

    except (ParseError, ValidationError) as e:
        abort(400, repr(e))


@app.route('/data/<data_group>/<data_type>/<data_set_id>', methods=['PATCH'])
@cache_control.nocache
@statsd.timer('write.route.data.patch.data_set')
def patch_by_group_type_and_id(data_group, data_type, data_set_id):
    """
    Patch by group, type and id
    e.g. PATCH https://BACKDROP/data/gcloud/sales/MjAxNi0wOC0xNSAwMDowMD
    """
    data_set_config = admin_api.get_data_set(data_group, data_type)

    _validate_config(data_set_config)
    _validate_auth(data_set_config)

    try:
        data = get_json_from_request(request)

        errors = _patch_data_set(data_set_config, data_set_id, data)

        if errors:
            return (jsonify(messages=errors), 400)
        else:
            return jsonify(status='ok')

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
    except ValidationError as e:
        return (jsonify(messages=[repr(e)]), 400)
    errors = _append_to_data_set(
        data_set_config,
        data)

    if errors:
        return (jsonify(messages=errors), 400)
    else:
        ok_message = ("Deprecation Warning: accessing by data-set name is "
                      "deprecated, Please use the /data-group/data-type form")
        return jsonify(status='ok',
                       message=ok_message)


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

    audit_delete(data_set_name)
    storage.delete_data_set(data_set_name)

    return jsonify(status='ok', message='Deleted {}'.format(data_set_name))


@app.route('/data/<data_group>/<data_type>/transform', methods=['POST'])
@cache_control.nocache
def transform_data_set(data_group, data_type):
    """
    Runs all transforms on the specified data. _start_at and _end_at
    are specify the date range to be used. _end_at defaults to now.
    TODO: allow the transform to be specified.
    """

    data_set_config = admin_api.get_data_set(data_group, data_type)
    _validate_config(data_set_config)
    _validate_auth(data_set_config)

    try:
        data = get_json_from_request(request)
    except ValidationError as e:
        return (jsonify(messages=[repr(e)]), 400)

    (start_at, end_at) = parse_bounding_dates(data)

    if start_at is None:
        abort(400, 'You must specify a _start_at timestamp')

    trigger_transforms(data_set_config, earliest=start_at, latest=end_at)

    return jsonify(status='ok')


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


def _append_to_data_set(data_set_config, data):
    audit_append(data_set_config['name'], data)
    data_set = DataSet(storage, data_set_config)
    data_set.create_if_not_exists()
    return data_set.store(data)


def _patch_data_set(data_set_config, data_set_id, data):
    audit_patch(data_set_config['name'], data)
    data_set = DataSet(storage, data_set_config)
    return data_set.patch(data_set_id, data)


def _delete_data_set(data_set_config, data_set_id):
    data_set = DataSet(storage, data_set_config)
    return data_set.delete(data_set_id)


def _empty_data_set(data_set_config):
    audit_delete(data_set_config['name'])
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


def bounding_dates(data):
    sorted_data = sorted(data, key=lambda datum: datum['_timestamp'])
    return sorted_data[0]['_timestamp'], sorted_data[-1]['_timestamp']


def parse_bounding_dates(data):
    if '_start_at' in data:
        start_at = datetime_parse(data['_start_at'])
        if '_end_at' in data:
            end_at = datetime_parse(data['_end_at'])
        else:
            end_at = datetime.datetime.now(pytz.UTC).replace(microsecond=0)
    else:
        return (None, None)

    return (start_at, end_at)


def trigger_transforms(data_set_config, data=[], earliest=None, latest=None):
    if len(data) > 0:
        earliest, latest = bounding_dates(data)

    if earliest is not None and latest is not None:
        celery_app.send_task('backdrop.transformers.dispatch.entrypoint',
                             args=(data_set_config['name'], earliest, latest))


def audit_append(data_set_name, data):
    if data:
        start_at, end_at = parse_bounding_dates(data)
        extra = {
            'token': request.headers.get('Authorization'),
            'data_set': data_set_name,
            'start_at': start_at,
            'end_at': end_at,
            'datapoints': len(data),
        }
        app.audit_logger.info("Data append action", extra=extra)


def audit_patch(data_set_name, data):
    if data:
        start_at, end_at = parse_bounding_dates(data)
        extra = {
            'token': request.headers.get('Authorization'),
            'data_set': data_set_name,
            'start_at': start_at,
            'end_at': end_at,
            'data': data,
        }
        app.audit_logger.info("Data patch action", extra=extra)


def audit_delete(data_set_name):
    app.audit_logger.info("Data delete action", extra={
        'token': request.headers.get('Authorization'),
        'data_set': data_set_name,
    })


def start(port):
    # this method only gets run on dev
    # app.debug = True
    app.run(host='0.0.0.0', port=port)
    app.logger.info("Backdrop Write API started")

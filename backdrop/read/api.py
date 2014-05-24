import datetime
import json
from os import getenv
from bson import ObjectId

from flask import Flask, jsonify, request
from flask_featureflags import FeatureFlag
from backdrop.read.query import Query

from .validation import validate_request_args
from ..core import database, log_handler, cache_control
from ..core.data_set import DataSet, NewDataSet
from ..core.database import InvalidOperationError
from ..core.repository import DataSetConfigRepository
from ..core.timeutils import as_utc

from ..core.storage.mongo import MongoStorageEngine


GOVUK_ENV = getenv("GOVUK_ENV", "development")

app = Flask("backdrop.read.api")

feature_flags = FeatureFlag(app)

# Configuration
app.config.from_object(
    "backdrop.read.config.{}".format(GOVUK_ENV))

db = database.Database(
    app.config['MONGO_HOSTS'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME']
)
storage = MongoStorageEngine.create(
    app.config['MONGO_HOSTS'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME'])

data_set_repository = DataSetConfigRepository(
    app.config['STAGECRAFT_URL'],
    app.config['STAGECRAFT_DATA_SET_QUERY_TOKEN'])

log_handler.set_up_logging(app, GOVUK_ENV)


class JsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return as_utc(obj).isoformat()
        return json.JSONEncoder.default(self, obj)
app.json_encoder = JsonEncoder


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

    app.logger.exception(e)
    error_message = 'Internal Server Error: {}'.format(repr(e))
    return (jsonify(status='error', message=error_message), 500)


@app.errorhandler(404)
@app.errorhandler(405)
def http_error_handler(e):
    app.logger.exception(e)
    return (jsonify(status='error',
                    message=getattr(e, 'name', 'Internal error')),
            getattr(e, 'code', 500))


@app.route('/_status', methods=['GET'])
@cache_control.nocache
def health_check():

    if not storage.alive():
        return jsonify(status='error',
                       message='cannot connect to database'), 500

    return jsonify(status='ok', message='database is up')


@app.route('/_status/data-sets', methods=['GET'])
@cache_control.nocache
def data_set_health():

    failing_data_sets = []
    okay_data_sets = []
    data_set_configs = data_set_repository.get_all()

    for data_set_config in data_set_configs:
        new_data_set = NewDataSet(storage, data_set_config)
        if not new_data_set.is_recent_enough():
            failing_data_sets.append({
                'name': new_data_set.name,
                'last_updated': new_data_set.get_last_updated()
            })
        else:
            okay_data_sets.append(new_data_set.name)

    if len(failing_data_sets):
        message = _data_set_message(failing_data_sets)
        if len(failing_data_sets) > 1:
            data_set_string = 'data_sets'
        else:
            data_set_string = 'data_set'

        return jsonify(status='error',
                       message='%s %s are out of date' %
                       (message, data_set_string)), 500

    else:
        return jsonify(status='ok',
                       message='(%s)\n All data_sets are in date' %
                       okay_data_sets)


def _data_set_message(data_sets):
    message = ', '.join(
        '%s (last updated: %s)' % (data_set['name'],
                                   data_set['last_updated'])
        for data_set in data_sets)
    return message


def log_error_and_respond(data_set, message, status_code):
    app.logger.error('%s: %s' % (data_set, message))
    return jsonify(status='error', message=message), status_code


@app.route('/data/<data_group>/<data_type>', methods=['GET', 'OPTIONS'])
def data(data_group, data_type):
    data_set_config = data_set_repository.get_data_set_for_query(data_group,
                                                                 data_type)
    return fetch(data_set_config)


@app.route('/<data_set_name>', methods=['GET', 'OPTIONS'])
@cache_control.etag
def query(data_set_name):
    data_set_config = data_set_repository.retrieve(data_set_name)
    return fetch(data_set_config)


def fetch(data_set_config):
    if data_set_config is None or not data_set_config.queryable:
        bname = "" if data_set_config is None else data_set_config.name + " "
        return log_error_and_respond(
            bname, 'data_set not found',
            404)

    if request.method == 'OPTIONS':
        # OPTIONS requests are made by XHR as part of the CORS spec
        # if the client uses custom headers
        response = app.make_default_options_response()
        response.headers['Access-Control-Max-Age'] = '86400'
        response.headers['Access-Control-Allow-Headers'] = 'cache-control'
    else:
        result = validate_request_args(request.args,
                                       data_set_config.raw_queries_allowed)

        if not result.is_valid:
            return log_error_and_respond(
                data_set_config.name, result.message,
                400)

        data_set = NewDataSet(storage, data_set_config)

        try:
            query = Query.parse(request.args)
            data = data_set.query(query)

        except InvalidOperationError:
            return log_error_and_respond(
                data_set.name, 'invalid collect function',
                400)

        response = jsonify(data=data)

    # allow requests from any origin
    response.headers['Access-Control-Allow-Origin'] = '*'

    response.headers['Cache-Control'] = "max-age=%d, must-revalidate" % \
                                        data_set_config.max_age

    return response


def start(port):
    app.debug = True
    app.run(host='0.0.0.0', port=port)

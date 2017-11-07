
import datetime
import json
from os import getenv

from bson import ObjectId
from flask import Flask, jsonify, request, make_response
from flask_featureflags import FeatureFlag
from performanceplatform import client

from backdrop import statsd
from .query import parse_query_from_request
from .validation import validate_request_args
from ..core import log_handler, cache_control, http_validation, parser
from ..core.data_set import DataSet
from ..core.errors import InvalidOperationError
from ..core.flaskutils import generate_request_id
from ..core.response import crossdomain
from ..core.storage.mongo import MongoStorageEngine
from ..core.timeutils import as_utc

ENVIRONMENT = getenv("ENVIRONMENT", "development")

app = Flask("backdrop.read.api")

feature_flags = FeatureFlag(app)

# Configuration
app.config.from_object(
    "backdrop.read.config.{}".format(ENVIRONMENT))

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

DEFAULT_DATA_SET_QUERYABLE = True
DEFAULT_DATA_SET_RAW_QUERIES = False
DEFAULT_DATA_SET_PUBLISHED = True
DEFAULT_DATA_SET_REALTIME = False

log_handler.set_up_logging(app, ENVIRONMENT)


class JsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return as_utc(obj).isoformat()
        return json.JSONEncoder.default(self, obj)
app.json_encoder = JsonEncoder


@app.errorhandler(500)
@crossdomain(origin='*')
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
@crossdomain(origin='*')
def http_error_handler(e):
    return (jsonify(status='error',
                    message=getattr(e, 'name', 'Internal error')),
            getattr(e, 'code', 500))


@app.route('/_status', methods=['GET'])
@crossdomain(origin='*')
@cache_control.nocache
@statsd.timer('read.route.heath_check.status')
def health_check():

    if not storage.alive():
        return jsonify(status='error',
                       message='cannot connect to database'), 500

    return jsonify(status='ok', message='database is up')


@app.route('/_status/data-sets', methods=['GET'])
@crossdomain(origin='*')
@cache_control.nocache
@statsd.timer('read.route.heath_check.data_set')
def data_set_health():

    failing_data_sets = []
    data_set_configs = admin_api.list_data_sets()
    data_sets = [DataSet(storage, config) for config in data_set_configs]

    storage.batch_last_updated(data_sets)

    for data_set in data_sets:
        if not data_set.is_recent_enough():
            failing_data_sets.append(
                _data_set_object(data_set)
            )

    if len(failing_data_sets):
        if len(failing_data_sets) > 1:
            data_set_string = 'data-sets are'
        else:
            data_set_string = 'data-set is'

        return jsonify(status='not okay',
                       data_sets=failing_data_sets,
                       message='%s %s out of date' %
                       (len(failing_data_sets), data_set_string)), 200

    else:
        return jsonify(status='ok',
                       data_sets=None,
                       message='All data_sets are in date')


def _data_set_object(data_set):
    return {
        "name": data_set.name,
        "seconds-out-of-date": data_set.get_seconds_out_of_date(),
        "last-updated": data_set.get_last_updated(),
        "max-age-expected": data_set.get_max_age_expected(),
    }


def log_error_and_respond(data_set, message, status_code):
    app.logger.error('%s: %s' % (data_set, message))
    return jsonify(status='error', message=message), status_code


def data_group_key():
    """Key used for rate-limiting requests to data-types"""
    return '{data_group}:{data_type}'.format(
        data_group=request.view_args.get('data_group'),
        data_type=request.view_args.get('data_type'))


@app.route('/data/<data_group>/<data_type>', methods=['GET', 'OPTIONS'])
def data(data_group, data_type):
    data_set_config = admin_api.get_data_set(data_group, data_type)
    return fetch(data_set_config)


def data_set_key():
    """Key used for rate-limiting requests to data sets"""
    return '{data_set_name}'.format(
        data_set_name=request.view_args.get('data_set_name'))


@app.route('/<data_set_name>', methods=['GET', 'OPTIONS'])
@http_validation.etag
def query(data_set_name):
    data_set_config = admin_api.get_data_set_by_name(data_set_name)
    return fetch(data_set_config)


@crossdomain(origin='*')
def fetch(data_set_config):
    error_text = 'data_set not found'

    if data_set_config is None:
        return log_error_and_respond('', error_text, 404)

    data_set_queryable = data_set_config.get('queryable',
                                             DEFAULT_DATA_SET_QUERYABLE)

    if not data_set_queryable:
        return log_error_and_respond(data_set_config['name'], error_text, 404)

    if request.method == 'OPTIONS':
        # OPTIONS requests are made by XHR as part of the CORS spec
        # if the client uses custom headers
        response = app.make_default_options_response()
        response.headers['Access-Control-Max-Age'] = '86400'
        response.headers[
            'Access-Control-Allow-Headers'] = \
            'cache-control, govuk-request-id, request-id'
    else:
        raw_queries_allowed = data_set_config.get(
            'raw_queries_allowed', DEFAULT_DATA_SET_RAW_QUERIES)
        result = validate_request_args(request.args, raw_queries_allowed)

        if not result.is_valid:
            return log_error_and_respond(
                data_set_config['name'], result.message,
                400)

        data_set = DataSet(storage, data_set_config)

        try:
            query = parse_query_from_request(request)
            data = data_set.execute_query(query)

        except InvalidOperationError:
            return log_error_and_respond(
                data_set.name, 'invalid collect function',
                400)

        data_set_is_published = data_set_config.get('published',
                                                    DEFAULT_DATA_SET_PUBLISHED)
        if data_set_is_published is False:
            warning = ("Warning: This data-set is unpublished. "
                       "Data may be subject to change or be inaccurate.")
            response = jsonify(data=data, warning=warning)
            # Do not cache unpublished data-sets
            response.headers['Cache-Control'] = "no-cache"
        else:
            fmt = to_csv if request.args.get("format") == "csv" else to_json
            response = fmt(data=data)

            # Set cache control based on data set type
            if data_set_config.get('realtime', DEFAULT_DATA_SET_REALTIME):
                cache_duration = 120
            else:
                cache_duration = 1800
            response.headers['Cache-Control'] = (
                "max-age=%d, "
                "must-revalidate" % cache_duration
            )

    return response


def to_csv(data, filename="export.csv"):
    csv = parser.json_to_csv(data=data)
    response = make_response(csv)
    content_disposition = "attachment; filename={}".format(filename)
    content_type = "text/csv"
    response.headers["Content-Disposition"] = content_disposition
    response.headers["Content-type"] = content_type
    return response


def to_json(data):
    response = jsonify(data=data)
    return response


def start(port):
    app.debug = True
    app.run(host='0.0.0.0', port=port)

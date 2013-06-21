import datetime
import json
from os import getenv
from bson import ObjectId

from flask import Flask, jsonify, request
from backdrop.core.log_handler \
    import create_request_logger, create_response_logger
from backdrop.read.response import SimpleData, PeriodData, WeeklyGroupedData
from backdrop.read.query import Query

from .validation import validate_request_args
from ..core import database, log_handler, cache_control
from ..core.bucket import Bucket


def setup_logging():
    log_handler.set_up_logging(app, "read", getenv("GOVUK_ENV", "development"))


app = Flask(__name__)

# Configuration
app.config.from_object(
    "backdrop.read.config.%s" % getenv("GOVUK_ENV", "development")
)

db = database.Database(
    app.config['MONGO_HOST'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME']
)

setup_logging()

app.before_request(create_request_logger(app))
app.after_request(create_response_logger(app))


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def raw_queries_allowed(bucket_name):
    raw_queries_config = app.config.get('RAW_QUERIES_ALLOWED', {})
    return bool(raw_queries_config.get(bucket_name, False))


@app.errorhandler(500)
@app.errorhandler(405)
@app.errorhandler(404)
def exception_handler(e):
    app.logger.exception(e)
    return jsonify(status='error', message=e.name), e.code


@app.route('/_status', methods=['GET'])
@cache_control.nocache
def health_check():
    if db.alive():
        return jsonify(status='ok', message='database seems fine')
    else:
        return jsonify(status='error',
                       message='cannot connect to database'), 500


@app.route('/<bucket_name>', methods=['GET', 'OPTIONS'])
@cache_control.set("max-age=3600, must-revalidate")
@cache_control.etag
def query(bucket_name):
    if request.method == 'OPTIONS':
        # OPTIONS requests are made by XHR as part of the CORS spec
        # if the client uses custom headers
        response = app.make_default_options_response()
        response.headers['Access-Control-Max-Age'] = '86400'
        response.headers['Access-Control-Allow-Headers'] = 'cache-control'
    else:
        result = validate_request_args(request.args,
                                       raw_queries_allowed(bucket_name))

        if not result.is_valid:
            app.logger.error(result.message)
            return jsonify(status='error', message=result.message), 400

        bucket = Bucket(db, bucket_name)
        result_data = bucket.query(Query.parse(request.args)).data()

        # Taken from flask.helpers.jsonify to add JSONEncoder
        # NB. this can be removed once fix #471 works it's way into a release
        # https://github.com/mitsuhiko/flask/pull/471
        json_data = json.dumps({"data": result_data}, cls=JsonEncoder,
                               indent=None if request.is_xhr else 2)

        response = app.response_class(json_data, mimetype='application/json')

    # allow requests from any origin
    response.headers['Access-Control-Allow-Origin'] = '*'

    return response


def start(port):
    app.debug = True
    app.run(host='0.0.0.0', port=port)

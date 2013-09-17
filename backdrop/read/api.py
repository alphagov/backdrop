import datetime
import json
from os import getenv
from bson import ObjectId

from flask import Flask, jsonify, request, redirect
from flask_featureflags import FeatureFlag
from backdrop.core.log_handler \
    import create_request_logger, create_response_logger
from backdrop.read.query import Query

from .validation import validate_request_args
from ..core import database, log_handler, cache_control
from ..core.bucket import Bucket
from ..core.database import InvalidOperationError
from ..core.repository import BucketRepository


def setup_logging():
    log_handler.set_up_logging(app, "read", getenv("GOVUK_ENV", "development"))


app = Flask(__name__)

feature_flags = FeatureFlag(app)

# Configuration
app.config.from_object(
    "backdrop.read.config.%s" % getenv("GOVUK_ENV", "development")
)

db = database.Database(
    app.config['MONGO_HOST'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME']
)

bucket_repository = BucketRepository(db.get_collection("buckets"))

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
app.json_encoder = JsonEncoder


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


def log_error_and_respond(message, status_code):
    app.logger.error(message)
    return jsonify(status='error', message=message), status_code


@app.route('/data/<service>/<data_type>', methods=['GET', 'OPTIONS'])
def service_data(service, data_type):
    bucket_config = bucket_repository.get_bucket_for_query(service, data_type)
    return query(bucket_config.name)


@app.route('/<bucket_name>', methods=['GET', 'OPTIONS'])
@cache_control.etag
def query(bucket_name):
    bucket_config = bucket_repository.retrieve(name=bucket_name)
    if bucket_config is None or not bucket_config.queryable:
        return log_error_and_respond('bucket not found', 404)

    if request.method == 'OPTIONS':
        # OPTIONS requests are made by XHR as part of the CORS spec
        # if the client uses custom headers
        response = app.make_default_options_response()
        response.headers['Access-Control-Max-Age'] = '86400'
        response.headers['Access-Control-Allow-Headers'] = 'cache-control'
    else:
        result = validate_request_args(request.args,
                                       bucket_config.raw_queries_allowed)

        if not result.is_valid:
            return log_error_and_respond(result.message, 400)

        bucket = Bucket(db, bucket_config)

        try:
            result_data = bucket.query(Query.parse(request.args)).data()
        except InvalidOperationError:
            return log_error_and_respond('invalid collect for that data', 400)

        response = jsonify(data=result_data)

    # allow requests from any origin
    response.headers['Access-Control-Allow-Origin'] = '*'

    max_age = 120 if bucket_config.realtime else 1800
    response.headers['Cache-Control'] = "max-age=%d, must-revalidate" % max_age

    return response


def start(port):
    app.debug = True
    app.run(host='0.0.0.0', port=port)

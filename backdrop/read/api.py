import datetime
import json
from os import getenv
from bson import ObjectId

from flask import Flask, jsonify, request
from flask_featureflags import FeatureFlag
from backdrop.read.query import Query

from .validation import validate_request_args
from ..core import database, log_handler, cache_control
from ..core.bucket import Bucket
from ..core.database import InvalidOperationError
from ..core.repository import BucketConfigRepository


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

bucket_repository = BucketConfigRepository(db)

log_handler.set_up_logging(app, GOVUK_ENV)


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
    return jsonify(
        status='error',
        message=getattr(e, 'name', 'Internal error')
    ), getattr(e, 'code', 500)


@app.route('/_status', methods=['GET'])
@cache_control.nocache
def health_check():

    if not db.alive():
        return jsonify(status='error',
                       message='cannot connect to database'), 500

    return jsonify(status='ok', message='database is up')


@app.route('/_status/buckets', methods=['GET'])
@cache_control.nocache
def bucket_health():

    failing_buckets = []
    okay_buckets = []
    bucket_configs = bucket_repository.get_all()

    for bucket_config in bucket_configs:
        bucket = Bucket(db, bucket_config)
        if not bucket.is_recent_enough():
            failing_buckets.append({
                'name': bucket.name,
                'last_updated': bucket.get_last_updated()
            })
        else:
            okay_buckets.append(bucket.name)

    if len(failing_buckets):
        message = _bucket_message(failing_buckets)
        buck_string = ((len(failing_buckets) > 1) and 'buckets' or 'bucket')

        return jsonify(status='error',
                       message='%s %s are out of date' %
                       (message, buck_string)), 500

    else:
        return jsonify(status='ok',
                       message='(%s)\n All buckets are in date' %
                       okay_buckets)


def _bucket_message(buckets):
    message = ', '.join(
        '%s (last updated: %s)' % (bucket['name'],
                                   bucket['last_updated'])
        for bucket in buckets)
    return message


def log_error_and_respond(bucket, message, status_code):
    app.logger.error('%s: %s' % (bucket, message))
    return jsonify(status='error', message=message), status_code


@app.route('/data/<data_group>/<data_type>', methods=['GET', 'OPTIONS'])
def data(data_group, data_type):
    bucket_config = bucket_repository.get_bucket_for_query(data_group,
                                                           data_type)
    return fetch(bucket_config)


@app.route('/<bucket_name>', methods=['GET', 'OPTIONS'])
@cache_control.etag
def query(bucket_name):
    bucket_config = bucket_repository.retrieve(name=bucket_name)
    return fetch(bucket_config)


def fetch(bucket_config):
    if bucket_config is None or not bucket_config.queryable:
        bname = "" if bucket_config is None else bucket_config.name + " "
        return log_error_and_respond(
            bname, 'bucket not found',
            404)

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
            return log_error_and_respond(
                bucket_config.name, result.message,
                400)

        bucket = Bucket(db, bucket_config)

        try:
            query = Query.parse(request.args)
            data = bucket.query(query).data()

        except InvalidOperationError:
            return log_error_and_respond(
                bucket.name, 'invalid collect function',
                400)

        response = jsonify(data=data)

    # allow requests from any origin
    response.headers['Access-Control-Allow-Origin'] = '*'

    response.headers['Cache-Control'] = "max-age=%d, must-revalidate" % \
                                        bucket_config.max_age

    return response


def start(port):
    app.debug = True
    app.run(host='0.0.0.0', port=port)

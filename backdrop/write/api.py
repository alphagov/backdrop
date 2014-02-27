from os import getenv
import json

from flask import Flask, request, jsonify, g
from flask_featureflags import FeatureFlag
from backdrop import statsd
from backdrop.core.bucket import Bucket
from backdrop.core.flaskutils import BucketConverter
from backdrop.core.repository import (BucketConfigRepository,
                                      UserConfigRepository)

from ..core.errors import ParseError, ValidationError
from ..core import database, log_handler, cache_control

from .validation import bearer_token_is_valid, extract_bearer_token


GOVUK_ENV = getenv("GOVUK_ENV", "development")

app = Flask("backdrop.write.api")

feature_flags = FeatureFlag(app)

# Configuration
app.config.from_object(
    "backdrop.write.config.{}".format(GOVUK_ENV))

db = database.Database(
    app.config['MONGO_HOSTS'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME']
)

with open('/var/apps/backdrop/test_output', 'a') as f:
    f.write("app.config['STAGECRAFT_URL']: " + app.config['STAGECRAFT_URL'] + '\n')

bucket_repository = BucketConfigRepository(
    'http://localhost:8080',
    #app.config['STAGECRAFT_URL'],
    app.config['STAGECRAFT_DATA_SET_QUERY_TOKEN'])

user_repository = UserConfigRepository(db)

log_handler.set_up_logging(app, GOVUK_ENV)

app.url_map.converters["bucket"] = BucketConverter


@app.errorhandler(500)
@app.errorhandler(405)
@app.errorhandler(404)
def exception_handler(e):
    app.logger.exception(e)

    bucket_name = getattr(g, 'bucket_name', request.path)
    statsd.incr("write.error", bucket=bucket_name)

    code = getattr(e, 'code', 500)
    name = getattr(e, 'name', "Internal Error")

    return jsonify(status='error', message=name), code


@app.route('/_status', methods=['GET'])
@cache_control.nocache
def health_check():
    if db.alive():
        return jsonify(status='ok', message='database seems fine')
    else:
        return jsonify(status='error',
                       message='cannot connect to database'), 500


@app.route('/data/<data_group>/<data_type>', methods=['POST'])
@cache_control.nocache
def write_by_group(data_group, data_type):
    """
    Write by group/type
    e.g. POST https://BACKDROP/data/my-transaction-name/volumetrics
    """
    bucket_config = bucket_repository.get_bucket_for_query(
        data_group,
        data_type)
    return _write_to_bucket(bucket_config)


@app.route('/<bucket:bucket_name>', methods=['POST'])
@cache_control.nocache
def post_to_bucket(bucket_name):
    bucket_config = bucket_repository.retrieve(name=bucket_name)
    return _write_to_bucket(bucket_config)


@app.route('/data-sets/<dataset_name>', methods=['POST'])
@cache_control.nocache
def create_collection_for_dataset(dataset_name):
    if not _allow_create_collection(request.headers.get('Authorization')):
        return jsonify(status='error',
                       message="Forbidden: invalid or no token given."), 403

    if db.collection_exists(dataset_name):
        return jsonify(status='error',
                       message='Collection exists with that name.'), 400

    try:
        data = json.loads(request.data)
    except ValueError as e:
        return jsonify(status='error', message=repr(e)), 400
    else:
        capped_size = data.get('capped_size', None)

    if capped_size is None or not isinstance(capped_size, int):
        return jsonify(
            status='error',
            message="You must specify an int capped_size of 0 or more"), 400

    if capped_size == 0:
        db.create_uncapped_collection(dataset_name)
    else:
        db.create_capped_collection(dataset_name, capped_size)

    return jsonify(status='ok', message='Created "{}"'.format(dataset_name))


def _allow_create_collection(auth_header):
    token = extract_bearer_token(auth_header)
    if token == app.config['CREATE_COLLECTION_ENDPOINT_TOKEN']:
        return True

    app.logger.info("Bad token for create collection: '{}'".format(token))
    return False


def _write_to_bucket(bucket_config):
    if bucket_config is None:
        return jsonify(status="error",
                       message='Could not find bucket_config'), 404

    g.bucket_name = bucket_config.name

    auth_header = request.headers.get('Authorization', None)

    if not bearer_token_is_valid(bucket_config, auth_header):
        statsd.incr("write_api.bad_token", bucket=g.bucket_name)
        return jsonify(status='error', message='Forbidden'), 403

    try:
        data = listify_json(request.json)

        bucket = Bucket(db, bucket_config)
        bucket.parse_and_store(data)

        return jsonify(status='ok')
    except (ParseError, ValidationError) as e:
        return jsonify(status="error", message=str(e)), 400


def listify_json(data):
    if data is None:
        raise ValidationError("Request must be JSON")

    if isinstance(data, list):
        return data
    else:
        return [data]


def start(port):
    # this method only gets run on dev
    # app.debug = True
    app.run(host='0.0.0.0', port=port)
    app.logger.info("Backdrop Write API started")

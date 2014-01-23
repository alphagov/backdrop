from os import getenv

from flask import Flask, request, jsonify, g, redirect, url_for
from flask_featureflags import FeatureFlag
from backdrop import statsd
from backdrop.core.bucket import Bucket
from backdrop.core.log_handler \
    import create_request_logger, create_response_logger
from backdrop.core.flaskutils import BucketConverter
from backdrop.core.repository import BucketConfigRepository,\
    UserConfigRepository

from ..core.errors import ParseError, ValidationError
from ..core import database, log_handler, cache_control

from .validation import bearer_token_is_valid


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

bucket_repository = BucketConfigRepository(db)
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
        data = load_json(request.json)

        bucket = Bucket(db, bucket_config)
        bucket.parse_and_store(data)

        return jsonify(status='ok')
    except (ParseError, ValidationError) as e:
        return jsonify(status="error", message=str(e)), 400


def load_json(data):
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

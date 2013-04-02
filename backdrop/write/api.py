from logging import FileHandler
import logging
from logging.handlers import RotatingFileHandler
from os import getenv

from flask import Flask, request, jsonify
from backdrop.core import records

from .validation import validate_post_to_bucket
from ..core import database
from ..core.bucket import Bucket


def environment():
    return getenv("GOVUK_ENV", "development")


app = Flask(__name__)

# Configuration
app.config.from_object(
    "backdrop.write.config.%s" % environment()
)

db = database.Database(
    app.config['MONGO_HOST'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME']
)


@app.before_request
def request_prehandler():
    log_this = "%s %s" % (request.method, request.url)
    if request.json:
        log_this += " JSON length: %i" % (len(request.json))
    app.logger.info(log_this)


@app.route('/_status')
def health_check():
    if db.alive():
        return jsonify(status='ok', message='database seems fine')
    else:
        return jsonify(status='error',
                       message='cannot connect to database'), 500


@app.route('/<bucket_name>', methods=['POST'])
def post_to_bucket(bucket_name):
    if not request.json:
        return jsonify(status='error', message='Request must be JSON'), 400

    incoming_data = prep_data(request.json)

    result = validate_post_to_bucket(incoming_data, bucket_name)

    # TODO: We currently don't test that incoming data gets validated
    # feels too heavy to be in the controller anyway - pull out later?
    if not result.is_valid:
        return jsonify(status='error', message=result.message), 400

    incoming_records = []

    for datum in incoming_data:
        incoming_records.append(records.parse(datum))

    bucket = Bucket(db, bucket_name)
    bucket.store(incoming_records)

    return jsonify(status='ok')


def setup_logger():
    handler = FileHandler("log/%s.log" % environment())
    handler.setLevel(app.config["LOG_LEVEL"])
    app.logger.addHandler(handler)


def prep_data(incoming_json):
    if isinstance(incoming_json, list):
        return incoming_json
    else:
        return [incoming_json]


def start(port):
    app.debug = True
    setup_logger()
    app.run(host='0.0.0.0', port=port)

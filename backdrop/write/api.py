from logging import FileHandler
import logging
from os import getenv

from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException
from backdrop.core import records
from backdrop.core.log_handler import get_log_file_handler

from .validation import validate_post_to_bucket
from ..core import database
from ..core.bucket import Bucket


def setup_logger():
    log_level = logging._levelNames[app.config['LOG_LEVEL']]
    app.logger.addHandler(
        get_log_file_handler("log/%s.write.log" % environment(), log_level))
    app.logger.setLevel(log_level)
    app.logger.info("Logging for Backdrop Write API started")


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


setup_logger()


@app.before_request
def request_prehandler():
    log_this = "%s %s" % (request.method, request.url)
    if request.json:
        log_this += " JSON length: %i" % (len(request.json))
    app.logger.info(log_this)


@app.errorhandler(500)
@app.errorhandler(405)
@app.errorhandler(404)
def exception_handler(e):
    app.logger.exception(e)
    return jsonify(status='error', message=''), e.code


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
        app.logger.error("Request must be JSON")
        return jsonify(status='error', message='Request must be JSON'), 400

    incoming_data = prep_data(request.json)

    result = validate_post_to_bucket(incoming_data, bucket_name)

    # TODO: We currently don't test that incoming data gets validated
    # feels too heavy to be in the controller anyway - pull out later?
    if not result.is_valid:
        app.logger.error(result.message)
        return jsonify(status='error', message=result.message), 400

    incoming_records = []

    for datum in incoming_data:
        incoming_records.append(records.parse(datum))

    bucket = Bucket(db, bucket_name)
    bucket.store(incoming_records)

    return jsonify(status='ok')


def prep_data(incoming_json):
    if isinstance(incoming_json, list):
        return incoming_json
    else:
        return [incoming_json]


def start(port):
    # this method only gets run on dev
    # app.debug = True
    app.run(host='0.0.0.0', port=port)
    app.logger.info("Backdrop Write API started")

from os import getenv

from flask import Flask, request, jsonify
from backdrop.core import records

from .validation import validate_post_to_bucket
from ..core import storage

app = Flask(__name__)

# Configuration
app.config.from_object(
    "backdrop.write.config.%s" % getenv("GOVUK_ENV", "development")
)

store = storage.Store(
    app.config['MONGO_HOST'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME']
)


@app.route('/_status')
def health_check():
    if store.alive():
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

    store.get_bucket(bucket_name).store(incoming_records)

    return jsonify(status='ok')


def prep_data(incoming_json):
    if isinstance(incoming_json, list):
        return incoming_json
    else:
        return [incoming_json]


def start(port):
    app.debug = True
    app.run(host='0.0.0.0', port=port)

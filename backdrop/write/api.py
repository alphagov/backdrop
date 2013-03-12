from os import getenv

from dateutil import parser
from flask import Flask, request, jsonify
import pytz

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

    if not result.is_valid:
        return jsonify(status='error', message=result.message), 400

    for data in incoming_data:
        if '_timestamp' in data:
            data['_timestamp'] = \
                time_string_to_utc_datetime(data['_timestamp'])

    store.get_bucket(bucket_name).store(incoming_data)

    return jsonify(status='ok')


def prep_data(incoming_json):
    if isinstance(incoming_json, list):
        return incoming_json
    else:
        return [incoming_json]


def time_string_to_utc_datetime(time_string):
    time = parser.parse(time_string)
    return time.astimezone(pytz.utc)


def start(port):
    app.debug = True
    app.run(host='0.0.0.0', port=port)

from os import getenv
from flask import Flask, request, jsonify
from dateutil import parser
from pymongo import MongoClient
import pytz
from ..core.validators import valid, invalid, bucket_is_valid, key_is_valid,\
    value_is_valid, value_is_valid_datetime_string, value_is_valid_id


app = Flask(__name__)

# Configuration
app.config.from_object(
    "performance_platform.write.config.%s" % getenv("FLASK_ENV", "development")
)

mongo = MongoClient('localhost', 27017)


@app.route('/_status')
def health_check():
    if mongo.alive():
        return jsonify(status='ok', message='database seems fine')
    else:
        return jsonify(status='500', message='cannot connect to database'), 500


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

    store_objects(bucket_name, incoming_data)
    return jsonify(status='ok')


def prep_data(incoming_json):
    if isinstance(incoming_json, list):
        return incoming_json
    else:
        return [incoming_json]


def validate_post_to_bucket(incoming_data, bucket_name):
    if not bucket_is_valid(bucket_name):
        return invalid('Bucket name is invalid')

    for datum in incoming_data:
        result = validate_data_object(datum)
        if not result.is_valid:
            return result

    return valid()


def validate_data_object(obj):
    for key, value in obj.items():
        if not key_is_valid(key):
            return invalid('{0} is not a valid key'.format(key))

        if not value_is_valid(value):
            return invalid('{0} is not a valid value'.format(value))

        if key == '_timestamp' and not value_is_valid_datetime_string(value):
            return invalid('{0} is not a valid timestamp'.format(value))

        if key == '_id' and not value_is_valid_id(value):
            return invalid('{0} is not a valid _id'.format(value))

    return valid()


def store_objects(bucket_name, objects_to_store):
    DataStore(app.config["DATABASE_NAME"]).store_data(
        objects_to_store,
        bucket_name
    )


def time_string_to_utc_datetime(time_string):
    time = parser.parse(time_string)
    return time.astimezone(pytz.utc)


class DataStore(object):
    def __init__(self, database_name):
        self.database = database_name

    def store_data(self, my_objects, collection_name):
        bucket = MongoClient('localhost', 27017)[self.database][
            collection_name]

        for data_objects in my_objects:
            bucket.save(data_objects)


def start(port):
    app.debug = True
    app.run(host='0.0.0.0', port=port)

from os import getenv
from flask import Flask
from flask import abort, request, Response
from dateutil import parser
from pymongo import MongoClient
import pytz
from ..core.validators import *


app = Flask(__name__)

# Configuration
app.config.from_object("performance_platform.write.config.%s" % getenv("FLASK_ENV", "development"))

mongo = MongoClient('localhost', 27017)


@app.route('/_status')
def health_check():
    if mongo.alive():
        return Response(
            '{"status":"ok","message":"database seems fine"}',
            mimetype='application/json'
        )
    else:
        return Response(
            '{"status":500,"message":"can''t connect to database"}',
            mimetype='application/json',
            status=500
        )


@app.route('/<bucket>', methods=['POST'])
def post_to_bucket(bucket):
    if not request_is_valid(request, bucket):
        abort(400)

    incoming_data = prep_data(request.json)

    if any(invalid_data_object(obj) for obj in incoming_data):
        abort(400)
    else:
        for data in incoming_data:
            if '_timestamp' in data:
                data['_timestamp'] = \
                    time_string_to_utc_datetime(data['_timestamp'])

        store_objects(bucket, incoming_data)
        return Response("{'status':'ok'}", mimetype='application/json')


def request_is_valid(request, bucket_name):
    if request.json and bucket_is_valid(bucket_name):
        return True
    else:
        return False


def prep_data(incoming_json):
    if isinstance(incoming_json, list):
        return incoming_json
    else:
        return [incoming_json]


def invalid_data_object(obj):
    for key, value in obj.items():
        if not key_is_valid(key) or not value_is_valid(value):
            print("step one {0} - {1}".format(key, value))
            return True
        if key == '_timestamp' and not value_is_valid_datetime_string(value):
            print("step two")
            return True
        if key == '_id' and not value_is_valid_id(value):
            print("step three")
            return True
    return False


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


def start():
    app.debug = True
    app.run(host='0.0.0.0', port=5001)

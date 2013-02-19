import re

from flask import Flask
from flask import abort, request, Response
from dateutil import parser
from pymongo import MongoClient
import pytz
from validators import value_is_valid_datetime_string, value_is_valid, \
    key_is_valid, bucket_is_valid


app = Flask(__name__)
mongo = MongoClient('localhost', 27017)

DATABASE_NAME = 'performance_platform'


@app.route('/_status/')
def health_check():
    if mongo.alive():
        return Response(
            "{'status':'ok','message':'database seems fine'}",
            mimetype='application/json'
        )
    else:
        return Response(
            "{'status':500,'message':'can't connect to ""database'}",
            mimetype='application/json',
            status=500
        )


@app.route('/<bucket>/', methods=['POST'])
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
            return True
        if key == '_timestamp' and not value_is_valid_datetime_string(value):
            return True
    return False


def store_objects(bucket_name, objects_to_store):
    bucket = mongo[DATABASE_NAME][bucket_name]
    bucket.insert(objects_to_store)


def time_string_to_utc_datetime(time_string):
    time = parser.parse(time_string)
    return time.astimezone(pytz.utc)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

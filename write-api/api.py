from flask import Flask
from flask import abort, request
from pymongo import MongoClient

import re

app = Flask(__name__)
mongo = MongoClient('localhost', 27017)

VALID_KEYWORD = re.compile('^[a-z0-9_\.-]+$')
VALID_BUCKET_NAME = re.compile('^[a-z0-9\.-][a-z0-9_\.-]*$')

RESERVED_KEYWORDS = (
    '_timestamp',
    '_start_at',
    '_end_at',
)


@app.route('/<bucket>/', methods=['POST'])
def post_to_bucket(bucket):
    if not request_is_valid(request, bucket):
        abort(400)

    incoming_data = prep_data(request.json)

    if any((not valid_json_object(obj)) for obj in incoming_data):
        abort(400)
    else:
        store_objects(bucket, incoming_data)
        return "{'status':'ok'}\n"


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


def valid_json_object(obj):
    for key, value in obj.items():
        if not key_is_valid(key) or not value_is_valid(value):
            return False
    return True


def bucket_is_valid(bucket_name):
    if VALID_BUCKET_NAME.match(bucket_name):
        return True
    return False


def key_is_valid(key):
    key = key.lower()
    if key[0] == '_':
        if key in RESERVED_KEYWORDS:
            return True
    else:
        if VALID_KEYWORD.match(key):
            return True
    return False


def value_is_valid(value):
    if type(value) == int:
        return True
    if type(value) == unicode:
        return True
    return False


def store_objects(bucket_name, objects_to_store):
    bucket = mongo['performance_platform'][bucket_name]
    bucket.insert(objects_to_store)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

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
    if not request.json or not bucket_is_valid(bucket):
        # explicit error out
        abort(400)

    if type(request.json) == list:
        incoming_objects = request.json
    else:
        incoming_objects = [request.json]

    if any((not valid_json_object(objects)) for objects in incoming_objects):
        abort(400)
    else:
        store_objects(bucket, incoming_objects)
        return "{'status':'ok'}\n"


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

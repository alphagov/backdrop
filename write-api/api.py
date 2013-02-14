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

valid_objects = []


@app.route('/<bucket>/', methods=['POST'])
def post_to_bucket(bucket):
    if request.json:
        if not bucket_is_valid(bucket):
            abort(400)
        if type(request.json) == list:
            # i am an array
            for obj in request.json:
                queue_json_object(obj)
        else:
            queue_json_object(request.json)
        store_valid_objects(bucket)
    else:
        abort(400)


def queue_json_object(obj):
    if valid_json_object(obj):
        print "APPEND", obj
        valid_objects.append(obj)


def valid_json_object(obj):
    for key, value in obj.items():
        if not key_is_valid(key) or not value_is_valid(value):
            abort(400)
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


def store_valid_objects(bucket_name):
    bucket = mongo['performance_platform'][bucket_name]
    bucket.insert(valid_objects)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

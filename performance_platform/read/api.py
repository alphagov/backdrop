from bson.code import Code
from dateutil import parser

from flask import Flask, jsonify, request, make_response, abort
from pymongo import MongoClient
from os import getenv
import pytz


# Configuration
from core.validators import value_is_valid_datetime_string

DATABASE_NAMES = {
    "development": "performance_platform",
    "test": "performance_platform_test"
}

app = Flask(__name__)
app.config.from_object(__name__)

mongo = MongoClient('localhost', 27017)


def open_bucket_collection(bucket):
    database_name = DATABASE_NAMES[getenv("FLASK_ENV", "development")]
    return mongo[database_name][bucket]


def validate_request_args(request_args):
    if 'start_at' in request_args:
        if not value_is_valid_datetime_string(request_args['start_at']):
            abort(400)
    if 'end_at' in request_args:
        if not value_is_valid_datetime_string(request_args['end_at']):
            abort(400)
    if 'filter_by' in request_args:
        if request_args['filter_by'].find(':') < 0:
            abort(400)


def build_query(request_args):
    query = {}

    if 'start_at' in request_args:
        query['_timestamp'] = {
            '$gte': parse_time_string(request_args['start_at'])
        }

    if 'end_at' in request_args:
        if '_timestamp' not in query:
            query['_timestamp'] = {}
        query['_timestamp']['$lt'] = parse_time_string(request_args['end_at'])

    if 'filter_by' in request_args:
        key, value = request_args['filter_by'].split(':', 1)
        query[key] = value

    return query


@app.route('/<bucket>', methods=['GET'])
def query(bucket):
    validate_request_args(request.args)

    collection = open_bucket_collection(bucket)

    query = build_query(request.args)

    result_data = []

    if 'group_by' in request.args:
        result = collection.group(
            key={request.args['group_by']: 1},
            condition=query,
            initial={'count': 0},
            reduce=Code("""
            function(current, previous) { previous.count++; }
            """)
        )

        for obj in result:
            result_data.append({obj[request.args['group_by']]: obj['count']})
    else:
        result = collection.find(query).sort("_timestamp", -1)

        for obj in result:
            string_id = str(obj.pop("_id"))
            obj['_id'] = string_id
            # TODO: mongo and timezones?!
            if "_timestamp" in obj:
                time = obj.pop("_timestamp")
                obj["_timestamp"] = time.replace(tzinfo=pytz.utc).isoformat()
            result_data.append(obj)

    # allow requests from any origin
    response = make_response(jsonify(data=result_data))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def parse_time_string(time_string):
    time = parser.parse(time_string)
    return time.astimezone(pytz.utc)


def jsonify_document(document):
    if '_timestamp' in document:
        document['_timestamp'] = document['_timestamp'].isoformat()

    return document


def start():
    app.debug = True
    app.run(host='0.0.0.0')

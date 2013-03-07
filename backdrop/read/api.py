from os import getenv

from bson.code import Code
from dateutil import parser
from flask import Flask, jsonify, request
from pymongo import MongoClient
import pytz

from .validation import validate_request_args


app = Flask(__name__)

# Configuration
app.config.from_object(
    "backdrop.read.config.%s" % getenv("GOVUK_ENV", "development")
)

mongo = MongoClient(app.config['MONGO_HOST'], app.config['MONGO_PORT'])


def open_bucket_collection(bucket):
    return mongo[app.config["DATABASE_NAME"]][bucket]


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
    result = validate_request_args(request.args)
    if not result.is_valid:
        return jsonify(status='error', message=result.message), 400

    collection = open_bucket_collection(bucket)

    query = build_query(request.args)

    result_data = []

    if 'group_by' in request.args:
        result = collection.group(
            key={request.args['group_by']: 1},
            condition=query,
            initial={'count': 0},
            reduce=Code("""
            function(current, previous)  { previous.count++; }
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
    response = jsonify(data=result_data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def parse_time_string(time_string):
    time = parser.parse(time_string)
    return time.astimezone(pytz.utc)


def start(port):
    app.debug = True
    app.run(host='0.0.0.0', port=port)

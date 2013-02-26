from bson.code import Code
from dateutil import parser

from flask import Flask, jsonify, request, make_response
from pymongo import MongoClient
import pytz


# Configuration
DATABASE_NAME = 'performance_platform'


app = Flask(__name__)
app.config.from_object(__name__)

mongo = MongoClient('localhost', 27017)


def open_bucket_collection(bucket):
    return mongo[app.config['DATABASE_NAME']][bucket]


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
    collection = open_bucket_collection(bucket)

    query = build_query(request.args)

    some_array = []

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
            some_array.append({obj[request.args['group_by']]: obj['count']})
    else:
        result = collection.find(query).sort("_timestamp", -1)

        for obj in result:
            string_id = str(obj.pop("_id"))
            obj['_id'] = string_id
            # TODO: mongo and timezones?!
            if "_timestamp" in obj:
                timestamp = obj.pop("_timestamp").replace(tzinfo=pytz.utc).isoformat()
                some_array.append({timestamp: obj})
            else:
                some_array.append(obj)


    # allow requests from any origin
    response = make_response(jsonify(data=some_array))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def parse_time_string(time_string):
    time = parser.parse(time_string)
    return time.astimezone(pytz.utc)


def jsonify_document(document):
    if '_timestamp' in document:
        document['_timestamp'] = document['_timestamp'].isoformat()

    return document

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

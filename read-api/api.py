from bson.code import Code
from dateutil import parser

from flask import Flask, jsonify, request
from pymongo import MongoClient
import pytz


# Configuration
DATABASE_NAME = 'performance_platform'


app = Flask(__name__)
app.config.from_object(__name__)

mongo = MongoClient('localhost', 27017)


def open_bucket_collection(bucket):
    return mongo[app.config['DATABASE_NAME']][bucket]


@app.route('/<bucket>', methods=['GET'])
def query(bucket):
    collection = open_bucket_collection(bucket)

    query = {}

    if 'start_at' in request.args:
        query['_timestamp'] = {
            '$gte': parse_time_string(request.args['start_at'])
        }

    if 'end_at' in request.args:
        if '_timestamp' not in query:
            query['_timestamp'] = {}
        query['_timestamp']['$lt'] = parse_time_string(request.args['end_at'])

    if 'filter_by' in request.args:
        key, value = request.args['filter_by'].split(':', 1)
        query[key] = value

    if 'group_by' in request.args:
        result = collection.group(
            key={request.args['group_by']: 1},
            condition=query,
            initial={'count': 0},
            reduce=Code("""
            function(current, previous) { previous.count++; }
            """)
        )
    else:
        result = collection.find(query)

    response_data = [
        jsonify_document(document) for document in result
    ]

    return jsonify(data=response_data)


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

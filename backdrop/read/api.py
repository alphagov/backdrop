import datetime
import json
from os import getenv

from dateutil import parser
from flask import Flask, jsonify, request
import pytz

from .validation import validate_request_args
from ..core import storage


app = Flask(__name__)

# Configuration
app.config.from_object(
    "backdrop.read.config.%s" % getenv("GOVUK_ENV", "development")
)

store = storage.Store(
    app.config['MONGO_HOST'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME']
)


def open_bucket_collection(bucket):
    return mongo[app.config["DATABASE_NAME"]][bucket]


def build_query(args):
    query = {}

    if 'start_at' in args:
        query['_timestamp'] = {
            '$gte': args['start_at']
        }

    if 'end_at' in args:
        if '_timestamp' not in query:
            query['_timestamp'] = {}
        query['_timestamp']['$lt'] = args['end_at']

    for key, value in args.get('filter_by', []):
        query[key] = value

    return query


def parse_request_args(request_args):
    args = {}

    if 'start_at' in request_args:
        args['start_at'] = parse_time_string(request_args['start_at'])
    if 'end_at' in request_args:
        args['end_at'] = parse_time_string(request_args['end_at'])

    args['filter_by'] = [
        f.split(':', 1) for f in request_args.getlist('filter_by')
    ]

    for key in ['group_by']:
        if key in request_args:
            args[key] = request_args[key]

    return args


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


@app.route('/<bucket_name>', methods=['GET'])
def query(bucket_name):
    result = validate_request_args(request.args)
    if not result.is_valid:
        return jsonify(status='error', message=result.message), 400
    args = parse_request_args(request.args)

    bucket = store.get_bucket(bucket_name)

    result_data = bucket.query(**args)

    # Taken from flask.helpers.jsonify to add JSONEncoder
    # NB. this can be removed once fix #471 works it's way into a release
    # https://github.com/mitsuhiko/flask/pull/471
    json_data = json.dumps({"data": result_data}, cls=JsonEncoder,
                           indent=None if request.is_xhr else 2)
    response = app.response_class(json_data, mimetype='application/json')

    # allow requests from any origin
    response.headers['Access-Control-Allow-Origin'] = '*'

    return response


def parse_time_string(time_string):
    time = parser.parse(time_string)
    return time.astimezone(pytz.utc)


def start(port):
    app.debug = True
    app.run(host='0.0.0.0', port=port)

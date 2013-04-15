import datetime
import json
from os import getenv

from dateutil import parser
from flask import Flask, jsonify, request
import pytz
from backdrop.core.log_handler \
    import create_request_logger, create_response_logger

from .validation import validate_request_args
from ..core import database, log_handler
from ..core.bucket import Bucket


def setup_logging():
    log_handler.set_up_logging(app, "read", getenv("GOVUK_ENV", "development"))


app = Flask(__name__)

# Configuration
app.config.from_object(
    "backdrop.read.config.%s" % getenv("GOVUK_ENV", "development")
)

db = database.Database(
    app.config['MONGO_HOST'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME']
)

setup_logging()

app.before_request(create_request_logger(app))
app.after_request(create_response_logger(app))


def parse_request_args(request_args):
    args = {}

    if 'start_at' in request_args:
        args['start_at'] = parse_time_string(request_args['start_at'])

    if 'end_at' in request_args:
        args['end_at'] = parse_time_string(request_args['end_at'])

    if 'filter_by' in request_args:
        args['filter_by'] = [
            f.split(':', 1) for f in request_args.getlist('filter_by')
        ]

    if 'period' in request_args:
        args['period'] = request_args['period']

    if 'group_by' in request_args:
        args['group_by'] = request_args['group_by']

    if 'sort_by' in request_args:
        args['sort_by'] = request_args['sort_by'].split(':', 1)

    if 'limit' in request_args:
        args['limit'] = int(request_args['limit'])

    if 'collect' in request_args:
        args['collect'] = request_args.getlist('collect')
    return args


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


@app.errorhandler(500)
@app.errorhandler(405)
@app.errorhandler(404)
def exception_handler(e):
    app.logger.exception(e)
    return jsonify(status='error', message=''), e.code


@app.route('/_status')
def health_check():
    if db.alive():
        return jsonify(status='ok', message='database seems fine')
    else:
        return jsonify(status='error',
                       message='cannot connect to database'), 500


@app.route('/<bucket_name>', methods=['GET'])
def query(bucket_name):
    result = validate_request_args(request.args)
    if not result.is_valid:
        app.logger.error(result.message)
        return jsonify(status='error', message=result.message), 400

    bucket = Bucket(db, bucket_name)
    result_data = bucket.query(**(parse_request_args(request.args)))

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

from os import getenv

from flask import Flask, request, jsonify, render_template, g, session, \
    redirect, url_for, flash
from backdrop import statsd
from backdrop.core.parse_csv import parse_csv
from backdrop.core.log_handler \
    import create_request_logger, create_response_logger
from backdrop.write.signonotron2 import Signonotron2, protected

from ..core.errors import ParseError, ValidationError
from ..core.validation import bucket_is_valid
from ..core import database, log_handler, records, cache_control
from ..core.bucket import Bucket

from .validation import bearer_token_is_valid

MAX_UPLOAD_SIZE = 100000


def setup_logging():
    log_handler.set_up_logging(app, "write",
                               getenv("GOVUK_ENV", "development"))


def environment():
    return getenv("GOVUK_ENV", "development")


app = Flask(__name__)

# Configuration
app.config.from_object(
    "backdrop.write.config.%s" % environment()
)
app.secret_key = app.config['SECRET_KEY']

db = database.Database(
    app.config['MONGO_HOST'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME']
)

setup_logging()

app.before_request(create_request_logger(app))
app.after_request(create_response_logger(app))

app.oauth_service = Signonotron2(
    client_id=app.config['CLIENT_ID'],
    client_secret=app.config['CLIENT_SECRET']
)


@app.route("/sign_in")
def oauth_login():
    return app.oauth_service.authorize()


@app.route("/sign_out")
def logout():
    session.clear()
    return render_template("signon/signout.html")


@app.route("/authorized")
def oauth_authorized():
    access_token = app.oauth_service.exchange(request.args['code'])

    user_details, can_see_backdrop = \
        app.oauth_service.user_details(access_token)
    if not can_see_backdrop:
        return redirect(url_for("not_authorized"))
    session.update(
        {"user": user_details["user"]["name"]})
    flash("You were successfully signed in")
    return redirect(url_for("index"))


@app.route("/not_authorized")
def not_authorized():
    return render_template("signon/not_authorized.html")


@app.errorhandler(500)
@app.errorhandler(405)
@app.errorhandler(404)
def exception_handler(e):
    app.logger.exception(e)
    statsd.incr("write.error", bucket=g.bucket_name)
    code = (e.code if hasattr(e, 'code') else None)
    return jsonify(status='error', message=''), code


@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")


@app.route('/_status', methods=['GET'])
@cache_control.nocache
def health_check():
    if db.alive():
        return jsonify(status='ok', message='database seems fine')
    else:
        return jsonify(status='error',
                       message='cannot connect to database'), 500


@app.route("/upload", methods=['GET'])
@protected
def upload_buckets():
    return "hello"


@app.route('/<bucket_name>', methods=['POST'])
@cache_control.nocache
def post_to_bucket(bucket_name):
    g.bucket_name = bucket_name

    if not bucket_is_valid(bucket_name):
        return jsonify(status="error",
                       message="Bucket name is invalid"), 400

    tokens = app.config['TOKENS']
    auth_header = request.headers.get('Authorization', None)

    if not bearer_token_is_valid(tokens, auth_header, bucket_name):
        statsd.incr("write_api.bad_token", bucket=g.bucket_name)
        return jsonify(status='error', message='Forbidden'), 403

    try:
        parse_and_store(
            load_json(request.json),
            bucket_name)

        return jsonify(status='ok')
    except (ParseError, ValidationError) as e:
        return jsonify(status="error", message=e.message), 400


@app.route('/<bucket_name>/upload', methods=['GET', 'POST'])
def upload(bucket_name):
    if not bucket_is_valid(bucket_name):
        return _invalid_upload("Bucket name is invalid")

    if request.method == 'GET':
        return render_template("upload_csv.html")

    return _store_csv_data(bucket_name)


def _store_csv_data(bucket_name):
    file_stream = request.files["file"].stream
    try:
        if request.content_length > MAX_UPLOAD_SIZE:
            return _invalid_upload("file too large")
        try:
            parse_and_store(
                parse_csv(file_stream),
                bucket_name)

            return render_template("upload_ok.html")
        except (ParseError, ValidationError) as e:
            return _invalid_upload(e.message)
    finally:
        file_stream.close()


def _invalid_upload(msg):
    return render_template("upload_error.html", message=msg), 400


def load_json(data):
    if data is None:
        raise ValidationError("Request must be JSON")

    if isinstance(data, list):
        return data
    else:
        return [data]


def parse_and_store(incoming_data, bucket_name):
    incoming_records = records.parse_all(incoming_data)

    app.logger.info(
        "request contains %s documents" % len(incoming_records))

    bucket = Bucket(db, bucket_name)
    bucket.store(incoming_records)


def start(port):
    # this method only gets run on dev
    # app.debug = True
    app.run(host='0.0.0.0', port=port)
    app.logger.info("Backdrop Write API started")

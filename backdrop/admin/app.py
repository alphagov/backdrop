from os import getenv
from functools import wraps

from flask import Flask, jsonify, url_for, request, \
    session, render_template, flash, redirect, abort

from .. import statsd
from backdrop.core import cache_control, log_handler
from backdrop.core.errors import ParseError, ValidationError
from backdrop.core.repository import (
    DataSetConfigRepository,
    get_user_repository)
from backdrop.core.storage.mongo import MongoStorageEngine
from backdrop.core.flaskutils import DataSetConverter
from backdrop.core.upload import create_parser
from .signonotron2 import Signonotron2
from .uploaded_file import UploadedFile, FileUploadError
from performanceplatform import client
from requests.exceptions import RequestException

GOVUK_ENV = getenv("GOVUK_ENV", "development")

app = Flask("backdrop.admin.app", static_url_path="/static")

# Configuration
app.config.from_object(
    "backdrop.admin.config.{}".format(GOVUK_ENV))

log_handler.set_up_logging(app, GOVUK_ENV)

app.url_map.converters["data_set"] = DataSetConverter

storage = MongoStorageEngine.create(
    app.config['MONGO_HOSTS'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME'])

data_set_repository = DataSetConfigRepository(
    app.config['STAGECRAFT_URL'],
    app.config['STAGECRAFT_DATA_SET_QUERY_TOKEN'])

user_repository = get_user_repository(app)


# TODO: move this out into a helper
def protected(f):
    @wraps(f)
    def verify_user_logged_in(*args, **kwargs):
        if not "user" in session:
            return redirect(
                url_for('oauth_sign_in'))
        return f(*args, **kwargs)
    return verify_user_logged_in


# Redirect from previous location
@app.route('/_user')
def old_index():
    return redirect(url_for("index")), 301


@app.errorhandler(500)
@app.errorhandler(405)
@app.errorhandler(404)
def exception_handler(e):
    app.logger.exception(e)

    data_set_name = getattr(e, 'data_set_name', request.path)
    statsd.incr("write.error", data_set=data_set_name)

    code = getattr(e, 'code', 500)
    name = getattr(e, 'name', 'Internal Error')

    return render_template("error.html",
                           name=name,
                           data_set_name=data_set_name), \
        code


@app.before_first_request
def setup_oauth_service():
    app.oauth_service = Signonotron2(
        client_id=app.config['OAUTH_CLIENT_ID'],
        client_secret=app.config['OAUTH_CLIENT_SECRET'],
        base_url=app.config['OAUTH_BASE_URL'],
        redirect_url=app.config['BACKDROP_ADMIN_UI_HOST']
        + url_for("oauth_authorized")
    )


@app.after_request
def prevent_clickjacking(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response


@app.route('/', methods=['GET'])
@cache_control.set("private, must-revalidate")
def index():
    """
    This representation is private to the logged-in user
    (with their own data_sets)
    """
    user_email = session.get('user', {}).get('email')
    if user_email:
        user_config = user_repository.retrieve(user_email)
    else:
        user_config = None

    return render_template("index.html", user_config=user_config)


@app.route('/_status', methods=['GET'])
@cache_control.nocache
def health_check():
    return jsonify(status='ok', message='all ok')


def _create_session_user(name, email):
    session.update(
        {"user": {
            "name": name,
            "email": email
        }})


if app.config.get('ALLOW_TEST_SIGNIN', True):
    @app.route('/sign-in/test', methods=['GET'])
    def oauth_test_signin():
        _create_session_user(request.args.get('user'),
                             request.args.get('email'))
        return "logged in as %s" % session.get('user'), 200


@app.route('/authorized', methods=['GET'])
@cache_control.nocache
def oauth_authorized():
    """
    The result of this is a redirect, which shouldn't be cached in
    case their permissions get changed, etc.
    """
    auth_code = request.args.get('code')
    if not auth_code:
        abort(400)
    access_token = app.oauth_service.exchange(auth_code)

    user_details, can_see_backdrop = \
        app.oauth_service.user_details(access_token)
    if can_see_backdrop is None:
        flash("Could not authenticate with single sign on.",
              category="error")
        return redirect(url_for("not_authorized"))
    if can_see_backdrop is False:
        flash("You are signed in to your GOV.UK account, "
              "but you don't have permissions to use this application.")
        return redirect(url_for("not_authorized"))
    _create_session_user(user_details["user"]["name"],
                         user_details["user"]["email"])
    flash("You were successfully signed in", category="success")
    return redirect(url_for("index"))


@app.route("/not-authorized")
@cache_control.nocache
def not_authorized():
    return render_template("signon/not_authorized.html")


@app.route("/sign-in")
@cache_control.nocache
def oauth_sign_in():
    """
    This returns a redirect to the OAuth provider, so we shouldn't
    allow this response to be cached.
    """
    return redirect(app.oauth_service.authorize())


@app.route("/sign-out")
@cache_control.set("private, must-revalidate")
def oauth_sign_out():
    session.clear()
    flash("You have been signed out of Backdrop", category="success")
    return render_template("signon/signout.html",
                           oauth_base_url=app.config['OAUTH_BASE_URL'])


@app.route('/<data_set:data_set_name>/upload', methods=['GET', 'POST'])
@protected
@cache_control.set("private, must-revalidate")
def upload(data_set_name):
    data_set_config = data_set_repository.retrieve(data_set_name)
    user_config = user_repository.retrieve(
        session.get("user").get("email"))

    if data_set_name not in user_config.data_sets:
        return abort(404)

    if request.method == 'GET':
        return render_template(
            "upload_{}.html".format(data_set_config.upload_format),
            data_set_name=data_set_name)

    return _store_data(data_set_config)


def _store_data(data_set_config):
    parse_file = create_parser(data_set_config)
    data_set = client.DataSet.from_group_and_type(
        app.config['BACKDROP_URL'] + '/data',
        data_set_config.data_group,
        data_set_config.data_type,
        token=data_set_config.bearer_token
    )
    expected_errors = (FileUploadError, ParseError, ValidationError)

    try:
        with UploadedFile(request.files['file']) as uploaded_file:
            raw_data = parse_file(uploaded_file.file_stream())
            data_set.post(raw_data)
    except expected_errors as e:
        log_upload_error('Upload error', app, e, data_set_config)
        return render_template('upload_error.html',
                               message=e.message,
                               data_set_name=data_set_config.name), 400
    except RequestException as e:
        log_upload_error('Error writing to backdrop', app, e, data_set_config)
        abort(500, 'Error saving to datastore: "{}"'.format(e.message))

    return render_template('upload_ok.html')


def log_upload_error(message, app, e, data_set_config):
        app.logger.error(
            '{}: {}'.format(message, e.message),
            extra={
                'backdrop_upload_error': type(e).__name__,
                'data_group': data_set_config.data_group,
                'data_type': data_set_config.data_type,
            },
            exc_info=True
        )


def start(port):
    app.debug = True
    app.run('0.0.0.0', port=port)

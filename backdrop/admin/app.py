from os import getenv
from functools import wraps

from flask import Flask, jsonify, url_for, request, \
    session, render_template, flash, redirect

from ..core import cache_control, log_handler, database
from ..core.log_handler \
    import create_request_logger, create_response_logger
from ..core.repository \
    import BucketConfigRepository, UserConfigRepository
from ..core.flaskutils import BucketConverter
from ..write.signonotron2 import Signonotron2

GOVUK_ENV = getenv("GOVUK_ENV", "development")

app = Flask("backdrop.admin.app", static_url_path="/static")

# Configuration
app.config.from_object(
    "backdrop.admin.config.{}".format(GOVUK_ENV))

log_handler.set_up_logging(app, GOVUK_ENV)

app.url_map.converters["bucket"] = BucketConverter

db = database.Database(
    app.config['MONGO_HOST'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME']
)

bucket_repository = BucketConfigRepository(db)
user_repository = UserConfigRepository(db)


# TODO: move this out into a helper
def protected(f):
    @wraps(f)
    def verify_user_logged_in(*args, **kwargs):
        if not "user" in session:
            return redirect(
                url_for('oauth_sign_in'))
        return f(*args, **kwargs)
    return verify_user_logged_in


@app.errorhandler(500)
@app.errorhandler(405)
@app.errorhandler(404)
def exception_handler(e):
    with open('test.rar.log', 'w+') as f:
        f.write("FOUND ERROR")
    app.logger.exception(e)

    return "ERROR", getattr(e, 'code', 500)


@app.before_first_request
def setup_oauth_service():
    app.oauth_service = Signonotron2(
        client_id=app.config['OAUTH_CLIENT_ID'],
        client_secret=app.config['OAUTH_CLIENT_SECRET'],
        base_url=app.config['OAUTH_BASE_URL'],
        redirect_url=app.config['BACKDROP_ADMIN_UI_HOST']
        + url_for("oauth_authorized")
    )
    app.logger.info("Setup oauth")


@app.after_request
def prevent_clickjacking(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response


@app.route('/', methods=['GET'])
@cache_control.set("private, must-revalidate")
def index():
    """
    This representation is private to the logged-in user
    (with their own buckets)
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
    return redirect(url_for("user_route"))


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


@app.route('/<bucket:bucket_name>/upload', methods=['GET', 'POST'])
@protected
@cache_control.set("private, must-revalidate")
def upload(bucket_name):
    bucket_config = bucket_repository.retrieve(bucket_name)
    user_config = user_repository.retrieve(
        session.get("user").get("email"))

    if bucket_name not in user_config.buckets:
        return abort(404)

    if request.method == 'GET':
        return render_template(
            "upload_{}.html".format(bucket_config.upload_format),
            bucket_name=bucket_name)
    return "hellp {}".format(user_config)


def start(port):
    app.debug = True
    app.run('0.0.0.0', port=port)

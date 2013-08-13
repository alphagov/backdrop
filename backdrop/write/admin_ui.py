from functools import wraps
from flask import flash, session, render_template, redirect, \
    request, abort
from admin_ui_helper import url_for
from backdrop.core.bucket import Bucket
from backdrop.core.errors import ParseError, ValidationError
from backdrop.core.upload import create_parser
from backdrop.core.upload.filters import first_sheet_filter
from backdrop.write.signonotron2 import Signonotron2
from ..core import cache_control


def setup(app, db):
    USER_SCOPE = app.config['USER_SCOPE']
    ADMIN_UI_HOST = app.config["BACKDROP_ADMIN_UI_HOST"]
    MAX_UPLOAD_SIZE = 100000

    app.oauth_service = Signonotron2(
        client_id=app.config['OAUTH_CLIENT_ID'],
        client_secret=app.config['OAUTH_CLIENT_SECRET'],
        base_url=app.config['OAUTH_BASE_URL'],
        backdrop_admin_ui_host=ADMIN_UI_HOST
    )

    @app.after_request
    def prevent_clickjacking(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        return response

    def protected(f):
        @wraps(f)
        def verify_user_logged_in(*args, **kwargs):
            if not "user" in session:
                return redirect(
                    url_for(ADMIN_UI_HOST, 'oauth_sign_in'))
            return f(*args, **kwargs)
        return verify_user_logged_in

    @app.route(USER_SCOPE)
    @cache_control.set("private, must-revalidate")
    def user_route():
        """
        This representation is private to the logged-in user
        (with their own buckets)
        """
        if use_single_sign_on(app):
            buckets_available = app.permissions.buckets_in_session(session)
            return render_template("index.html",
                                   buckets_available=buckets_available)
        else:
            return "Backdrop is running."

    @app.route(USER_SCOPE + "/sign_in")
    @cache_control.nocache
    def oauth_sign_in():
        """
        This returns a redirect to the OAuth provider, so we shouldn't
        allow this response to be cached.
        """
        return app.oauth_service.authorize()

    @app.route(USER_SCOPE + "/sign_out")
    @cache_control.set("private, must-revalidate")
    def oauth_sign_out():
        session.clear()
        flash("You have been signed out of Backdrop", category="success")
        return render_template("signon/signout.html",
                               oauth_base_url=app.config['OAUTH_BASE_URL'])

    @app.route(USER_SCOPE + "/authorized")
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
            return redirect(url_for(ADMIN_UI_HOST, "not_authorized"))
        if can_see_backdrop is False:
            flash("You are signed in to your GOV.UK account, "
                  "but you don't have permissions to use this application.")
            return redirect(url_for(ADMIN_UI_HOST, "not_authorized"))
        _create_session_user(user_details["user"]["name"],
                             user_details["user"]["email"])
        flash("You were successfully signed in", category="success")
        return redirect(url_for(ADMIN_UI_HOST, "user_route"))

    @app.route(USER_SCOPE + "/not_authorized")
    @cache_control.nocache
    def not_authorized():
        return render_template("signon/not_authorized.html")

    @app.route(USER_SCOPE + "/protected", methods=['GET'])
    @protected
    def upload_buckets():
        return "hello"

    if allow_test_signin(app):
        @app.route(USER_SCOPE + "/sign_in/test", methods=['GET'])
        def test_signin():
            _create_session_user(request.args.get('user'),
                                 request.args.get('email'))
            return "logged in as %s" % session.get('user'), 200

    def _create_session_user(name, email):
        session.update(
            {"user": {
                "name": name,
                "email": email
            }})

    @app.route('/<bucket:bucket_name>/upload', methods=['GET', 'POST'])
    @protected
    @cache_control.set("private, must-revalidate")
    def upload(bucket_name):
        current_user_email = session.get("user").get("email")
        if not app.permissions.allowed(current_user_email, bucket_name):
            return abort(404)

        upload_format = _upload_format_for(bucket_name)
        upload_filters = _upload_filters_for(bucket_name)

        if request.method == 'GET':
            return render_template("upload_%s.html" % upload_format,
                                   bucket_name=bucket_name)

        parser = create_parser(upload_format, upload_filters)

        return _store_data(bucket_name, parser)

    def _store_data(bucket_name, parser):
        file_stream = request.files["file"].stream
        if not request.files["file"].filename:
            return _invalid_upload("file is required")
        try:
            if request.content_length > MAX_UPLOAD_SIZE:
                return _invalid_upload("file too large")
            try:
                data = parser(file_stream)

                auto_id_keys = _auto_id_keys_for(bucket_name)
                bucket = Bucket(db, bucket_name, generate_id_from=auto_id_keys)
                bucket.parse_and_store(data)

                return render_template("upload_ok.html")
            except (ParseError, ValidationError) as e:
                return _invalid_upload(e.message)
        finally:
            file_stream.close()

    def _upload_format_for(bucket_name):
        return app.config.get("BUCKET_UPLOAD_FORMAT", {})\
                         .get(bucket_name, "csv")

    def _upload_filters_for(bucket_name):
        return app.config.get("BUCKET_UPLOAD_FILTERS", {})\
                         .get(bucket_name, [first_sheet_filter])

    def _auto_id_keys_for(bucket_name):
        return app.config.get("BUCKET_AUTO_ID_KEYS", {}).get(bucket_name)

    def _invalid_upload(msg):
        app.logger.error("Upload error: %s" % msg)
        return render_template("upload_error.html", message=msg), 400


def allow_test_signin(app):
    return bool(app.config.get("ALLOW_TEST_SIGNIN"))


def use_single_sign_on(app):
    return bool(app.config.get("SINGLE_SIGN_ON"))

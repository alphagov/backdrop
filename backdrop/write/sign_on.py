from functools import wraps
from flask import flash, session, render_template, redirect, \
    request, abort
from admin_ui_helper import url_for
from backdrop.write.signonotron2 import Signonotron2


def setup(app):
    USER_SCOPE = app.config['USER_SCOPE']
    ADMIN_UI_HOST = app.config["BACKDROP_ADMIN_UI_HOST"]

    app.oauth_service = Signonotron2(
        client_id=app.config['OAUTH_CLIENT_ID'],
        client_secret=app.config['OAUTH_CLIENT_SECRET'],
        base_url=app.config['OAUTH_BASE_URL'],
        backdrop_admin_ui_host=ADMIN_UI_HOST
    )

    def protected(f):
        @wraps(f)
        def verify_user_logged_in(*args, **kwargs):
            if not "user" in session:
                return redirect(
                    url_for(ADMIN_UI_HOST, 'oauth_sign_in'))
            return f(*args, **kwargs)
        return verify_user_logged_in

    @app.route(USER_SCOPE)
    def user_route():
        if use_single_sign_on(app):
            return render_template("index.html")
        else:
            return "Backdrop is running."

    @app.route(USER_SCOPE + "/sign_in")
    def oauth_sign_in():
        return app.oauth_service.authorize()

    @app.route(USER_SCOPE + "/sign_out")
    def oauth_sign_out():
        session.clear()
        flash("You have been signed out of Backdrop", category="success")
        return render_template("signon/signout.html")

    @app.route(USER_SCOPE + "/authorized")
    def oauth_authorized():
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


def allow_test_signin(app):
    return bool(app.config.get("ALLOW_TEST_SIGNIN"))


def use_single_sign_on(app):
    return bool(app.config.get("SINGLE_SIGN_ON"))

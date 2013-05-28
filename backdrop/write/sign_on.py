from flask import flash, session, render_template, redirect, url_for, request
from backdrop.write.signonotron2 import protected, Signonotron2

NON_BUCKET_SCOPE = "/_user"


def setup(app):
    app.oauth_service = Signonotron2(
        client_id=app.config['CLIENT_ID'],
        client_secret=app.config['CLIENT_SECRET']
    )

    @app.route(NON_BUCKET_SCOPE + "/sign_in")
    def oauth_sign_in():
        return app.oauth_service.authorize()

    @app.route(NON_BUCKET_SCOPE + "/sign_out")
    def oauth_sign_out():
        session.clear()
        flash("You have been signed out of Backdrop", category="success")
        return render_template("signon/signout.html")

    @app.route(NON_BUCKET_SCOPE + "/authorized")
    def oauth_authorized():
        access_token = app.oauth_service.exchange(request.args.get('code'))

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
        session.update(
            {"user": user_details["user"]["name"]})
        flash("You were successfully signed in", category="success")
        return redirect(url_for("index"))

    @app.route(NON_BUCKET_SCOPE + "/not_authorized")
    def not_authorized():
        return render_template("signon/not_authorized.html")

    @app.route(NON_BUCKET_SCOPE + "/protected", methods=['GET'])
    @protected
    def upload_buckets():
        return "hello"


def use_single_sign_on(app):
    return bool(app.config.get("SINGLE_SIGN_ON"))

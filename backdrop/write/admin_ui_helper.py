from flask import url_for as flask_url_for


def url_for(admin_ui_host, method_name):
    return admin_ui_host + flask_url_for(method_name)

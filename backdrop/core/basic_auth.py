from functools import wraps
from flask import Flask, request, jsonify

def check_auth(username, password, required_username, required_password):
    return username == required_username and password == required_password

def authenticate():
    return jsonify(error="requires authentication", status="401"), 401

def requires_auth(username='admin', password='password'):
    def func_wrapper(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password, username, password):
                return authenticate()
            return func(*args, **kwargs)
        return decorated
    return func_wrapper



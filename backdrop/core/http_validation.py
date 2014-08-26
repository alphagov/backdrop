"""
HTTP Validation decorators for flask apps
See http://tools.ietf.org/html/rfc7234#section-4.3
"""
import hashlib
from flask import make_response, request
from functools import wraps


def etag(func):
    @wraps(func)
    def new_func(*args, **kwargs):
        resp = make_response(func(*args, **kwargs))
        resp.set_etag(hashlib.sha1(resp.data).hexdigest())
        resp.make_conditional(request)
        return resp

    return new_func

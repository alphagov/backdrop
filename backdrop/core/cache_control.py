"""
Cache control decorators for flask apps
"""
import hashlib
from flask import make_response, request
from functools import wraps


def nocache(func):
    return set("no-cache")(func)


def set(cache_control):
    """Decorator that applies cache control headers to flask response
    """
    def decorator(func):
        @wraps(func)
        def new_func(*args, **kwargs):
            resp = make_response(func(*args, **kwargs))
            resp.headers['Cache-Control'] = cache_control
            return resp
        return new_func
    return decorator


def etag(func):
    @wraps(func)
    def new_func(*args, **kwargs):
        resp = make_response(func(*args, **kwargs))
        resp.set_etag(hashlib.sha1(resp.data).hexdigest())
        resp.make_conditional(request)
        return resp

    return new_func

"""
Common auth checks for writing.
"""
from flask import abort, g, request
from functools import wraps

from .validation import auth_header_is_valid, extract_bearer_token


def check(admin_api):
    """Decorator that does auth checks prior to storing data.
    """
    def decorator(func):
        @wraps(func)
        def new_func(*args, **kwargs):
            data_group = request.view_args['data_group']
            data_type = request.view_args['data_type']
            g.data_set_config = admin_api.get_data_set(data_group, data_type)
            _validate_config(g.data_set_config)
            _validate_auth(g.data_set_config)
            return func(*args, **kwargs)
        return new_func
    return decorator


def _validate_auth(data_set_config):
    try:
        auth_header = request.headers['Authorization']
    except KeyError:
        abort(401, 'Expected header of form: Authorization: Bearer <token>')

    if not auth_header_is_valid(data_set_config, auth_header):
        token = extract_bearer_token(auth_header)
        abort(401,
              'Unauthorized: Invalid bearer token \'{0}\' for \'{1}\''.format(
                  token, data_set_config['name']))


def _validate_config(data_set_config):
    if data_set_config is None:
        abort(404, 'Could not find data_set_config')

    g.data_set_name = data_set_config['name']

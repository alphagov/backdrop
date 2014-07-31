from functools import wraps

from mock import patch
from contextlib import contextmanager


@contextmanager
def pretend_this_data_set_exists(data_set_config):
    """Patches methods on the performanceplatform-client that respond to queries
    for data sets to respond with valid data set configuration"""
    try:
        namespace = 'performanceplatform.client.AdminAPI'
        with patch(namespace + '.get_data_set') as get_data_set:
            with patch(namespace + '.get_data_set_by_name') as get_data_set_by_name:
                with patch(namespace + '.list_data_sets') as list_data_sets:
                    def get_data_set_side_effect(data_group, data_type):
                        if (data_group == data_set_config['data_group']
                                and data_type == data_set_config['data_type']):
                            return data_set_config

                    def get_data_set_by_name_side_effect(name):
                        if name == data_set_config['name']:
                            return data_set_config

                    get_data_set.side_effect = get_data_set_side_effect
                    get_data_set_by_name.side_effect = get_data_set_by_name_side_effect
                    list_data_sets.side_effect = NotImplementedError(
                        "The method to list data sets is not patched yet")
                    yield
    finally:
        pass  # NOTE: delete the collection in Mongo here


def fake_data_set_exists(name, data_group="group", data_type="type",
                         *data_set_args, **data_set_kwargs):
    setup_data_set_name = name

    def decorator(func):
        @wraps(func)
        def wrapped_fake_data_set_exists(*args, **kwargs):
            base_config = {
                'name': setup_data_set_name,
                'data_group': data_group,
                'data_type': data_type,
                'capped_size': 0,
            }
            config = dict(base_config.items() + data_set_kwargs.items())
            with pretend_this_data_set_exists(config):
                func(*args, **kwargs)
        return wrapped_fake_data_set_exists
    return decorator


def fake_no_data_sets_exist():
    """Ensures that all methods on the performanceplatform-client that respond
    to queries for data sets return None or empty lists"""
    def decorator(func):
        @wraps(func)
        def wrapped_fake_no_data_sets_exist(*args, **kwargs):
            namespace = 'performanceplatform.client.AdminAPI'
            with patch(namespace + '.get_data_set') as get_data_set:
                with patch(namespace + '.get_data_set_by_name') as get_data_set_by_name:
                    with patch(namespace + '.list_data_sets') as list_data_sets:
                        get_data_set.return_value = None
                        get_data_set_by_name.return_value = None
                        list_data_sets.return_value = []

                        func(*args, **kwargs)

        return wrapped_fake_no_data_sets_exist
    return decorator


def stub_user_retrieve_by_email(email, data_sets=None):
    """Returns a user object by patching the performanceplatform-client"""
    setup_user_email = email

    def decorator(func):
        @wraps(func)
        def wrapped_stub_user_retrieve_by_name(*args, **kwargs):
            with patch('performanceplatform.client.AdminAPI.get_user') as get_user:
                def side_effect(email):
                    if email == setup_user_email:
                        return {'email': email, 'data_sets': data_sets}
                get_user.side_effect = side_effect
                func(*args, **kwargs)
        return wrapped_stub_user_retrieve_by_name
    return decorator

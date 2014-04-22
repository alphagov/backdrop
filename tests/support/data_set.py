from functools import wraps

from mock import patch
from contextlib import contextmanager

from backdrop.core.data_set import DataSetConfig
from backdrop.core.user import UserConfig


@contextmanager
def pretend_this_data_set_exists(data_set_config):
    # NOTE: To fake this really accurately, one could *actually* create the
    # collections with the config provided (ie capped size). As it stands,
    # a collection will be automatically created by Mongo when written to. This
    # will not use the capped_size specified in data_set_config.
    try:
        namespace = 'backdrop.core.repository.DataSetConfigRepository'
        with patch(namespace + '.retrieve') as retrieve:
            with patch(namespace + '.get_data_set_for_query') as query:
                with patch(namespace + '.get_all') as get_all:
                    def retrieve_side_effect(name):
                        if name == data_set_config.name:
                            return data_set_config

                    def query_side_effect(data_group, data_type):
                        if (data_group == data_set_config.data_group
                                and data_type == data_set_config.data_type):
                            return data_set_config

                    retrieve.side_effect = retrieve_side_effect
                    query.side_effect = query_side_effect
                    get_all.side_effect = NotImplementedError(
                        "Need to patch get_all")
                    yield
    finally:
        pass  # NOTE: delete the collection in Mongo here


def fake_data_set_exists(name, data_group="group", data_type="type",
                       *data_set_args, **data_set_kwargs):
    setup_data_set_name = name

    def decorator(func):
        @wraps(func)
        def wrapped_fake_data_set_exists(*args, **kwargs):
            with pretend_this_data_set_exists(
                    DataSetConfig(
                        setup_data_set_name,
                        data_group,
                        data_type,
                        *data_set_args,
                        **data_set_kwargs)):
                func(*args, **kwargs)
        return wrapped_fake_data_set_exists
    return decorator


def fake_no_data_sets_exist():
    def decorator(func):
        @wraps(func)
        def wrapped_fake_no_data_sets_exist(*args, **kwargs):
            namespace = 'backdrop.core.repository.DataSetConfigRepository'
            with patch(namespace + '.retrieve') as retrieve:
                with patch(namespace + '.get_data_set_for_query') as query:
                    with patch(namespace + '.get_all') as get_all:
                        retrieve.return_value = None
                        query.return_value = None
                        get_all.return_value = []

                        func(*args, **kwargs)

        return wrapped_fake_no_data_sets_exist
    return decorator


def stub_user_retrieve_by_email(email, data_sets=None):
    setup_user_email = email

    def decorator(func):
        @wraps(func)
        def wrapped_stub_user_retrieve_by_name(*args, **kwargs):
            namespace = 'backdrop.core.repository.UserConfigRepository'
            with patch(namespace + '.retrieve') as retrieve:
                def side_effect(email):
                    if email == setup_user_email:
                        return UserConfig(email, data_sets)
                retrieve.side_effect = side_effect
                func(*args, **kwargs)
        return wrapped_stub_user_retrieve_by_name
    return decorator

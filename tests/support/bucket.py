from functools import wraps

from mock import patch
from contextlib import contextmanager

from backdrop.core.bucket import BucketConfig
from backdrop.core.user import UserConfig


@contextmanager
def pretend_this_bucket_exists(bucket_config):
    # NOTE: To fake this really accurately, one could *actually* create the
    # collections with the config provided (ie capped size). As it stands,
    # a collection will be automatically created by Mongo when written to. This
    # will not use the capped_size specified in bucket_config.
    try:
        namespace = 'backdrop.core.repository.BucketConfigRepository'
        with patch(namespace + '.retrieve') as retrieve:
            with patch(namespace + '.get_bucket_for_query') as query:
                with patch(namespace + '.get_all') as get_all:
                    def retrieve_side_effect(name):
                        if name == bucket_config.name:
                            return bucket_config

                    def query_side_effect(data_group, data_type):
                        if (data_group == bucket_config.data_group
                                and data_type == bucket_config.data_type):
                            return bucket_config

                    retrieve.side_effect = retrieve_side_effect
                    query.side_effect = query_side_effect
                    get_all.side_effect = NotImplementedError(
                        "Need to patch get_all")
                    yield
    finally:
        pass  # NOTE: delete the collection in Mongo here


def fake_bucket_exists(name, data_group="group", data_type="type",
                       *bucket_args, **bucket_kwargs):
    setup_bucket_name = name

    def decorator(func):
        @wraps(func)
        def wrapped_fake_bucket_exists(*args, **kwargs):
            with pretend_this_bucket_exists(
                    BucketConfig(
                        setup_bucket_name,
                        data_group,
                        data_type,
                        *bucket_args,
                        **bucket_kwargs)):
                func(*args, **kwargs)
        return wrapped_fake_bucket_exists
    return decorator


def fake_no_buckets_exist():
    def decorator(func):
        @wraps(func)
        def wrapped_fake_no_buckets_exist(*args, **kwargs):
            namespace = 'backdrop.core.repository.BucketConfigRepository'
            with patch(namespace + '.retrieve') as retrieve:
                with patch(namespace + '.get_bucket_for_query') as query:
                    with patch(namespace + '.get_all') as get_all:
                        retrieve.return_value = None
                        query.return_value = None
                        get_all.return_value = []

                        func(*args, **kwargs)

        return wrapped_fake_no_buckets_exist
    return decorator


def stub_user_retrieve_by_email(email, buckets=None):
    setup_user_email = email

    def decorator(func):
        @wraps(func)
        def wrapped_stub_user_retrieve_by_name(*args, **kwargs):
            namespace = 'backdrop.core.repository.UserConfigRepository'
            with patch(namespace + '.retrieve') as retrieve:
                def side_effect(email):
                    if email == setup_user_email:
                        return UserConfig(email, buckets)
                retrieve.side_effect = side_effect
                func(*args, **kwargs)
        return wrapped_stub_user_retrieve_by_name
    return decorator

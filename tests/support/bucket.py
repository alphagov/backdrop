from functools import wraps

from mock import patch
from backdrop.core.bucket import BucketConfig
from backdrop.core.user import UserConfig
from backdrop.write.api import bucket_repository


def stub_bucket_retrieve_by_name(name, data_group="group", data_type="type", *bucket_args, **bucket_kwargs):
    setup_bucket_name = name

    def decorator(func):
        @wraps(func)
        def wrapped_stub_bucket_retrieve_by_name(*args, **kwargs):
            with patch('backdrop.core.repository.BucketConfigRepository.retrieve') as retrieve:
                def side_effect(name):
                    if name == setup_bucket_name:
                        return BucketConfig(setup_bucket_name, data_group, data_type, *bucket_args, **bucket_kwargs)
                retrieve.side_effect = side_effect
                func(*args, **kwargs)
        return wrapped_stub_bucket_retrieve_by_name
    return decorator


def setup_bucket(name, *bucket_args, **bucket_kwargs):
    setup_bucket_name = name

    def decorator(func):
        @wraps(func)
        def wrapped_setup_bucket(*args, **kwargs):
            bucket = BucketConfig(setup_bucket_name, *bucket_args, **bucket_kwargs)
            bucket_repository.save(bucket)
            func(*args, **kwargs)
            bucket_repository._repository.collection._collection.remove({"_id": setup_bucket_name})
        return wrapped_setup_bucket
    return decorator


def stub_user_retrieve_by_email(email, buckets=None):
    setup_user_email = email

    def decorator(func):
        @wraps(func)
        def wrapped_stub_user_retrieve_by_name(*args, **kwargs):
            with patch('backdrop.core.repository.UserConfigRepository.retrieve') as retrieve:
                def side_effect(email):
                    if email == setup_user_email:
                        return UserConfig(email, buckets)
                retrieve.side_effect = side_effect
                func(*args, **kwargs)
        return wrapped_stub_user_retrieve_by_name
    return decorator

from functools import wraps

from mock import patch
from backdrop.core.bucket import BucketConfig


def setup_bucket(name, *bucket_args, **bucket_kwargs):
    setup_bucket_name = name

    def decorator(func):
        @wraps(func)
        def wrapped_setup_bucket(*args, **kwargs):
            with patch('backdrop.core.repository.BucketRepository.retrieve') as retrieve:
                def side_effect(name):
                    if name == setup_bucket_name:
                        return BucketConfig(setup_bucket_name, *bucket_args, **bucket_kwargs)
                retrieve.side_effect = side_effect
                func(*args, **kwargs)
        return wrapped_setup_bucket
    return decorator

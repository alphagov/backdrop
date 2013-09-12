from functools import wraps

from mock import patch
from backdrop.core.bucket import BucketConfig


def setup_bucket(*bucket_args, **bucket_kwargs):
    def decorator(func):
        @wraps(func)
        def wrapped_setup_bucket(*args, **kwargs):
            with patch('backdrop.core.repository.BucketRepository.retrieve') as retrieve:
                retrieve.return_value = BucketConfig(*bucket_args, **bucket_kwargs)
                func(*args, **kwargs)
        return wrapped_setup_bucket
    return decorator

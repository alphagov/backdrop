from functools import wraps

from mock import patch

from backdrop.core.bucket_new import Bucket


def setup_bucket(name):
    def decorator(func):
        @wraps(func)
        def wrapped_setup_bucket(*args, **kwargs):
            with patch('backdrop.core.repository.BucketRepository.retrieve') as retrieve:
                retrieve.return_value = Bucket(name=name)
                func(*args, **kwargs)
        return wrapped_setup_bucket
    return decorator

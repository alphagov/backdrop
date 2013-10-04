from functools import wraps
from mock import patch


def stub_clamscan(is_virus=False):
    def decorator(func):
        @wraps(func)
        def wrapped_stub_clamscan(*args, **kwargs):
            with patch('backdrop.write.scanned_file.ScannedFile._clamscan') as clamscan:
                clamscan.return_value = is_virus
                func(*args, **kwargs)
        return wrapped_stub_clamscan
    return decorator

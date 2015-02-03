from functools import wraps


class BackdropError(StandardError):
    pass


class ParseError(BackdropError):
    pass


class ValidationError(BackdropError):
    pass


class DataSetCreationError(BackdropError):
    pass


class InvalidSortError(ValueError):
    pass


class InvalidOperationError(ValueError):

    """Raised if an invalid collect function is provided, or if an error
    is raised from a collect function"""
    pass


def incr_on_error(stats_client, metric_name):
    """
    Increments metric_name if func() raises an exception, then
    re-raises the exception.
    """

    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except:
                stats_client.incr(metric_name)
                raise
        return wrapped
    return decorator

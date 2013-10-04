from collections import namedtuple


def _bucket_list_is_valid(buckets):
    if not isinstance(buckets, list):
        return False

    is_string = lambda value: isinstance(value, basestring)

    return all(map(is_string, buckets))


_UserConfig = namedtuple(
    "_UserConfig",
    "email buckets")


class UserConfig(_UserConfig):
    def __new__(cls, email, buckets=None):
        if buckets is None:
            buckets = []
        elif not _bucket_list_is_valid(buckets):
            raise ValueError("buckets must be a list of bucket names")

        return super(UserConfig, cls).__new__(cls, email, buckets)

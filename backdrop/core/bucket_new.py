from .validation import bucket_is_valid


class Bucket(object):
    def __init__(self, name, raw_queries_allowed=False):
        if not bucket_is_valid(name):
            raise ValueError("Bucket name is not valid")

        self._bucket_settings = {
            "name": name,
            "raw_queries_allowed": raw_queries_allowed,
        }

    @property
    def name(self):
        return self._bucket_settings["name"]

    @property
    def raw_queries_allowed(self):
        return self._bucket_settings["raw_queries_allowed"]

    def __eq__(self, other):
        if other is None:
            return False
        return self._bucket_settings == other._bucket_settings

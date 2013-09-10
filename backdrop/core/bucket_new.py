from .validation import bucket_is_valid


class Bucket(object):
    def __init__(self, name):
        if not bucket_is_valid(name):
            raise ValueError("Bucket name is not valid")

        self._bucket_settings = {
            "name": name
        }

    @property
    def name(self):
        return self._bucket_settings["name"]

    def __eq__(self, other):
        if other is None:
            return False
        return self._bucket_settings == other._bucket_settings

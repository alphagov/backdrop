class Permissions(object):
    def __init__(self, permissions):
        self._permissions = permissions

    def is_user_allowed_to_bucket(self, user, bucket_name):
        return user in self._permissions[bucket_name]

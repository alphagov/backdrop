class Permissions(object):
    def __init__(self, permissions):
        self._permissions = permissions

    def allowed(self, user, bucket_name):
        return bucket_name in self._permissions.get(user, [])

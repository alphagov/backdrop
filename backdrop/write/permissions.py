class Permissions(object):
    def __init__(self, permissions):
        self._permissions = permissions

    def allowed(self, user, bucket_name):
        return bucket_name in self._permissions.get(user, [])

    def buckets_in_session(self, session):
        if session.get("user"):
            email = session.get("user").get("email")
            return self._permissions.get(email, [])
        else:
            return []

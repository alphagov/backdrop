from backdrop.core.bucket import BucketConfig
from backdrop.core.user import UserConfig


class BucketConfigRepository(object):
    def __init__(self, db):
        self._db = db
        self._collection = db.get_collection("buckets")

    def save(self, bucket_config, create_bucket=True):
        if not isinstance(bucket_config, BucketConfig):
            raise ValueError("Expected BucketConfig")

        doc = {
            "_id": bucket_config.name,
        }
        doc.update(bucket_config._asdict())

        if bucket_config.realtime and create_bucket:
            self._db.create_capped_collection(bucket_config.name,
                                              bucket_config.capped_size)

        self._collection.save(doc)

    def retrieve(self, name):
        return self._query_first({"name": name})

    def get_bucket_for_query(self, data_group, data_type):
        return self._query_first({"data_group": data_group,
                                  "data_type": data_type})

    def _query_first(self, params):
        doc = self._collection.find_one(params)
        if doc is None:
            return None
        del doc["_id"]
        return BucketConfig(**doc)


class UserConfigRepository(object):
    def __init__(self, db):
        self._db = db
        self._collection = db.get_collection("users")

    def save(self, user_config):
        if not isinstance(user_config, UserConfig):
            raise ValueError("Expected UserConfig")

        doc = {
            "_id": user_config.email,
        }
        doc.update(user_config._asdict())

        self._collection.save(doc)

    def retrieve(self, email):
        return self._query_first({"email": email})

    def _query_first(self, params):
        doc = self._collection.find_one(params)
        if doc is None:
            return None
        del doc["_id"]
        return UserConfig(**doc)

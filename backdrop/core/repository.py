from backdrop.core.bucket import BucketConfig
from backdrop.core.user import UserConfig


class _Repository(object):
    def __init__(self, db, model_cls, collection_name, id_field):
        self.db = db
        self.model_cls = model_cls
        self.collection_name = collection_name
        self.id_field = id_field
        self.collection = db.get_collection(self.collection_name)

    def save(self, model):
        if not isinstance(model, self.model_cls):
            raise ValueError("Expected {0}".format(self.model_cls.__name__))

        doc = {
            "_id": getattr(model, self.id_field)
        }
        doc.update(model._asdict())

        self.collection.save(doc)

    def retrieve(self, value):
        return self.query_first({self.id_field: value})

    def query_first(self, params):
        doc = self.collection.find_one(params)
        if doc is None:
            return None
        del doc["_id"]
        return self.model_cls(**doc)


class BucketConfigRepository(object):
    def __init__(self, db):
        self._db = db
        self._repository = _Repository(db, BucketConfig, "buckets", "name")

    def save(self, bucket_config, create_bucket=True):
        self._repository.save(bucket_config)

        if bucket_config.realtime and create_bucket:
            self._db.create_capped_collection(bucket_config.name,
                                              bucket_config.capped_size)

    def retrieve(self, name):
        return self._repository.retrieve(name)

    def get_bucket_for_query(self, data_group, data_type):
        return self._repository.query_first({"data_group": data_group,
                                             "data_type": data_type})


class UserConfigRepository(object):
    def __init__(self, db):
        self._db = db
        self._repository = _Repository(db, UserConfig, "users", "email")

    def save(self, user_config):
        self._repository.save(user_config)

    def retrieve(self, email):
        return self._repository.retrieve(email)

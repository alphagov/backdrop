from backdrop.core.bucket import BucketConfig


class BucketRepository(object):
    def __init__(self, db):
        self._collection = db.get_collection("buckets")

    def save(self, bucket):
        if not isinstance(bucket, BucketConfig):
            raise ValueError("Expected BucketConfig")

        doc = {
            "_id": bucket.name,
        }
        doc.update(bucket._asdict())

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

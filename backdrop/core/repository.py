from backdrop.core.bucket import BucketConfig


class BucketRepository(object):
    def __init__(self, collection):
        self._collection = collection

    def save(self, bucket):
        if not isinstance(bucket, BucketConfig):
            raise ValueError("Expected BucketConfig")

        doc = {
            "_id": bucket.name,
        }
        doc.update(bucket._asdict())

        self._collection.save(doc)

    def retrieve(self, name):
        doc = self._collection.find_one({"name": name})
        if doc is None:
            return None
        del doc["_id"]
        return BucketConfig(**doc)

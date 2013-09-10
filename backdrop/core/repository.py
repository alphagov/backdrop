from .bucket_new import Bucket


class BucketRepository(object):
    def __init__(self, collection):
        self._collection = collection

    def save(self, bucket):
        doc = {
            "_id": bucket.name,
            "name": bucket.name,
            "raw_queries_allowed": bucket.raw_queries_allowed,
        }
        self._collection.save(doc)

    def retrieve(self, name):
        doc = self._collection.find_one({"name": name})
        if doc is None:
            return None
        del doc["_id"]
        return Bucket(**doc)

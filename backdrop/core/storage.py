from pymongo.mongo_client import MongoClient


class Store(object):
    def __init__(self, host, port, name):
        self._mongo = MongoClient(host, port)
        self.name = name

    def alive(self):
        return self._mongo.alive()

    def get_bucket(self, name):
        return Bucket(self, name)

    @property
    def client(self):
        return self._mongo

    @property
    def database(self):
        return self.client[self.name]


class Bucket(object):
    def __init__(self, store, name):
        self._store = store
        self.name = name

    @property
    def _collection(self):
        return self._store.database[self.name]

    def store(self, item):
        self._collection.save(item)

    def store_many(self, items):
        [self._collection.save(item) for item in items]

    def all(self):
        return self._collection.find()

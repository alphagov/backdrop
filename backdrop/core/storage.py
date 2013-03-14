from bson.code import Code
from pymongo.mongo_client import MongoClient
import pytz


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

    def _store_one(self, record):
        self._collection.save(record.to_mongo())

    def store(self, records):
        if isinstance(records, list):
            [self._store_one(record) for record in records]
        else:
            self._store_one(records)

    def all(self):
        return self._collection.find()

    def query(
            self, start_at=None, end_at=None, group_by=None, filter_by=None):
        query = {}
        if start_at:
            query['_timestamp'] = {
                '$gte': start_at
            }
        if end_at:
            if '_timestamp' not in query:
                query['_timestamp'] = {}
            query['_timestamp']['$lt'] = end_at

        if filter_by:
            for key, value in filter_by:
                query[key] = value

        result = []
        if group_by:
            cursor = self._collection.group(
                key=[group_by],
                condition=query,
                initial={'count': 0},
                reduce=Code("""
                function(current, previous) { previous.count++; }
                """)
            )

            result = [{doc[group_by]: doc['count']} for doc in cursor]
        else:
            cursor = self._collection.find(query).sort('_timestamp', -1)

            for doc in cursor:
                # stringify the id
                doc['_id'] = str(doc['_id'])
                if '_timestamp' in doc:
                    doc['_timestamp'] = doc['_timestamp'].replace(
                        tzinfo=pytz.UTC)
                result.append(doc)

        return result

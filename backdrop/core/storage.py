import datetime
from pymongo.mongo_client import MongoClient
import pytz
from backdrop.core.repository import Repository


def utc(dt):
    return dt.replace(tzinfo=pytz.UTC)


class Store(object):
    def __init__(self, host, port, name):
        self._mongo = MongoClient(host, port)
        self.name = name

    def alive(self):
        return self._mongo.alive()

    def get_bucket(self, name):
        return Bucket(Repository(self.database[name]))

    @property
    def client(self):
        return self._mongo

    @property
    def database(self):
        return self.client[self.name]


class Bucket(object):
    def __init__(self, repository):
        self.repository = repository

    def store(self, records):
        if isinstance(records, list):
            [self.repository.save(record.to_mongo()) for record in records]
        else:
            self.repository.save(records.to_mongo())

    def all(self):
        return self.repository.all()

    def _period_group(self, doc):
        start = utc(doc['_week_start_at'])
        return {
            '_start_at': start,
            '_end_at': start + datetime.timedelta(days=7),
            'count': doc['count']
        }

    def execute_grouped_query(self, group_by, query):
        cursor = self.repository.group(group_by, query)
        result = [{doc[group_by]: doc['count']} for doc in cursor]
        return result

    def execute_period_query(self, query):
        cursor = self.repository.group('_week_start_at', query)
        result = [self._period_group(doc) for doc in cursor]
        return result

    def execute_query(self, query):
        result = []
        cursor = self.repository.find(query)
        for doc in cursor:
            # stringify the id
            doc['_id'] = str(doc['_id'])
            if '_timestamp' in doc:
                doc['_timestamp'] = utc(doc['_timestamp'])
            result.append(doc)
        return result

    def query(self,
              start_at=None,
              end_at=None,
              group_by=None,
              filter_by=None,
              period=None):

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

        if group_by:
            result = self.execute_grouped_query(group_by, query)
        elif period:
            result = self.execute_period_query(query)
        else:
            result = self.execute_query(query)

        return result

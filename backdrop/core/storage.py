import datetime
from pymongo.mongo_client import MongoClient
import pytz
from backdrop.core.repository import Repository, build_query


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

    def _period_group(self, doc):
        start = utc(doc['_week_start_at'])
        return {
            '_start_at': start,
            '_end_at': start + datetime.timedelta(days=7),
            'count': doc['count']
        }

    def execute_binary_group_query(self, key1, key2, query):
        result = []
        cursor = self.repository.multi_group(key1, key2, query)
        for doc in cursor:
            week_start_at = doc.pop('_week_start_at')
            doc['_start_at'] = week_start_at
            doc['_end_at'] = week_start_at + datetime.timedelta(days=7)
            result.append(doc)
        return result

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

    def query(self, **params):
        query = build_query(**params)

        if 'group_by' in params and 'period' in params:
            result = self.execute_binary_group_query(
                params['group_by'],
                params['period'],
                query
            )
        elif 'group_by' in params:
            result = self.execute_grouped_query(params['group_by'], query)
        elif 'period' in params:
            result = self.execute_period_query(query)
        else:
            result = self.execute_query(query)

        return result

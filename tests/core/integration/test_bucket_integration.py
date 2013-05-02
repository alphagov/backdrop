import unittest
from mock import patch, call

from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase
from hamcrest import *

from backdrop.core import database, bucket
from backdrop.core.records import Record
from backdrop.read.query import Query
from tests.support.test_helpers import d_tz

HOST = 'localhost'
PORT = 27017
DB_NAME = 'performance_platform_test'
BUCKET = 'bucket_integration_test'


class TestBucketIntegration(unittest.TestCase):
    def setUp(self):
        self.db = database.Database(HOST, PORT, DB_NAME)
        self.bucket = bucket.Bucket(self.db, BUCKET)
        self.mongo_collection = MongoClient(HOST, PORT)[DB_NAME][BUCKET]

    def setup__timestamp_data(self):
        self.mongo_collection.save({
            "_id": 'last',
            "_timestamp": d_tz(2013, 3, 1),
            "_week_start_at": d_tz(2013, 2, 25)
        })
        self.mongo_collection.save({
            "_id": 'first',
            "_timestamp": d_tz(2013, 1, 1),
            "_week_start_at": d_tz(2012, 12, 31)
        })
        self.mongo_collection.save({
            "_id": 'second',
            "_timestamp": d_tz(2013, 2, 1),
            "_week_start_at": d_tz(2013, 1, 28)
        })

    def tearDown(self):
        self.mongo_collection.drop()

    def test_that_records_get_sent_to_mongo_correctly(self):
        my_record = Record({'foo': 'bar'})
        self.bucket.store(my_record)

        collection = self.mongo_collection.find()
        assert_that(list(collection), only_contains(
            has_entries({"foo": "bar"})
        ))

    def test_that_a_list_of_records_get_sent_to_mongo_correctly(self):
        my_records = [
            Record({'name': 'Groucho'}),
            Record({'name': 'Harpo'}),
            Record({'name': 'Chico'})
        ]

        self.bucket.store(my_records)

        collection = self.mongo_collection.find()
        assert_that(list(collection), only_contains(
            has_entries({'name': 'Groucho'}),
            has_entries({'name': 'Harpo'}),
            has_entries({'name': 'Chico'})
        ))

    def test_period_queries_get_sorted_by__week_start_at(self):
        self.setup__timestamp_data()
        query = Query.create()
        result = query.execute_period_query(self.bucket.repository)
        assert_that(result, contains(
            has_entry('_start_at', d_tz(2012, 12, 31)),
            has_entry('_start_at', d_tz(2013, 1, 28)),
            has_entry('_start_at', d_tz(2013, 2, 25))
        ))

import unittest
from mock import patch, call

from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase
from hamcrest import *

from backdrop.core import database, bucket
from backdrop.core.records import Record

HOST = 'localhost'
PORT = 27017
DB_NAME = 'performance_platform_test'
BUCKET = 'bucket_integration_test'


class TestBucketIntegration(unittest.TestCase):
    def setUp(self):
        self.db = database.Database(HOST, PORT, DB_NAME)
        self.bucket = bucket.Bucket(self.db, BUCKET)
        self.mongo_collection = MongoClient(HOST, PORT)[DB_NAME][BUCKET]

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

import unittest
from mock import patch, call

from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase
from hamcrest import *

from backdrop.core import storage
from backdrop.core.records import Record


class TestStore(unittest.TestCase):
    def setUp(self):
        self.store = storage.Store('localhost', 27017, 'backdrop_test')

    def test_alive(self):
        assert_that(self.store.alive(), is_(True))

    def test_getting_a_bucket(self):
        bucket = self.store.get_bucket('my_bucket')

        print "TODO: move to repository tests"
        # assert_that(bucket.name, is_("my_bucket"))

    def test_getting_the_mongo_client(self):
        assert_that(self.store.client, instance_of(MongoClient))

    def test_getting_the_mongo_database(self):
        assert_that(self.store.database, instance_of(MongoDatabase))


class TestBucket(unittest.TestCase):
    def setUp(self):
        self.store = storage.Store('localhost', 27017, 'backdrop_test')
        self.bucket = storage.Bucket(self.store, 'my_bucket')

    def tearDown(self):
        # TODO: verify these no longer touch the DB
        self.store.client.drop_database('backdrop_test')

    @patch("pymongo.collection.Collection.save")
    def test_that_records_get_sent_to_mongo_correctly(self, save):
        my_record = Record({'foo': 'bar'})
        self.bucket.store(my_record)
        save.assert_called_with({'foo': 'bar'})

    @patch("pymongo.collection.Collection.save")
    def test_that_a_list_of_records_get_sent_to_mongo_correctly(self, save):
        my_records = [
            Record({'name': 'Groucho'}),
            Record({'name': 'Harpo'}),
            Record({'name': 'Chico'})
        ]

        self.bucket.store(my_records)

        save.assert_has_calls([
            call({'name': 'Groucho'}),
            call({'name': 'Harpo'}),
            call({'name': 'Chico'})
        ])

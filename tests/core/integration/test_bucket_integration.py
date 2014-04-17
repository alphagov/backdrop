import unittest
from mock import patch, call
import datetime

from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase
from hamcrest import *

from backdrop.core import database, data_set
from backdrop.core.data_set import BucketConfig
from backdrop.core.records import Record
from backdrop.core.timeseries import WEEK
from backdrop.read.query import Query
from tests.support.test_helpers import d_tz

HOST = ['localhost']
PORT = 27017
DB_NAME = 'performance_platform_test'
BUCKET = 'data_set_integration_test'


class TestBucketIntegration(unittest.TestCase):

    def setUp(self):
        self.db = database.Database(HOST, PORT, DB_NAME)
        self.data_set = data_set.Bucket(
            self.db, BucketConfig(BUCKET, data_group="group", data_type="type", max_age_expected=1000))
        self.mongo_collection = MongoClient(HOST, PORT)[DB_NAME][BUCKET]

    def setup__timestamp_data(self):
        self.mongo_collection.save({
            "_id": 'last',
            "_timestamp": d_tz(2013, 3, 1),
            "_week_start_at": d_tz(2013, 2, 25),
            "_updated_at": d_tz(2013, 8, 10)
        })
        self.mongo_collection.save({
            "_id": 'first',
            "_timestamp": d_tz(2013, 1, 1),
            "_week_start_at": d_tz(2012, 12, 31),
            "_updated_at": d_tz(2013, 9, 10)
        })
        self.mongo_collection.save({
            "_id": 'second',
            "_timestamp": d_tz(2013, 2, 1),
            "_week_start_at": d_tz(2013, 1, 28),
            "_updated_at": d_tz(2013, 10, 10)
        })

    def tearDown(self):
        self.mongo_collection.drop()

    def test_that_records_get_sent_to_mongo_correctly(self):
        my_record = Record({'foo': 'bar'})
        self.data_set.store(my_record)

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

        self.data_set.store(my_records)

        collection = self.mongo_collection.find()
        assert_that(list(collection), only_contains(
            has_entries({'name': 'Groucho'}),
            has_entries({'name': 'Harpo'}),
            has_entries({'name': 'Chico'})
        ))

    def test_period_queries_get_sorted_by__week_start_at(self):
        self.setup__timestamp_data()
        query = Query.create(period=WEEK)
        result = query.execute(self.data_set.repository)
        assert_that(result.data(), contains(
            has_entry('_start_at', d_tz(2012, 12, 31)),
            has_entry('_start_at', d_tz(2013, 1, 28)),
            has_entry('_start_at', d_tz(2013, 2, 25))
        ))

    def test_data_set_returns_last_updated(self):
        self.setup__timestamp_data()
        assert_that(self.data_set.get_last_updated(),
                    equal_to(d_tz(2013, 10, 10)))

    def test_data_set_returns_none_if_there_is_no_last_updated(self):
        assert_that(self.data_set.get_last_updated(), is_(None))

    def test_data_set_is_recent_enough(self):
        self.mongo_collection.save({
            "_id": "first",
            "_updated_at": datetime.datetime.now() - datetime.timedelta(seconds=500)
        })
        assert_that(self.data_set.is_recent_enough())

    def test_data_set_is_not_recent_enough(self):
        self.mongo_collection.save({
            "_id": "first",
            "_updated_at": datetime.datetime.now() - datetime.timedelta(seconds=50000)
        })
        assert_that(not self.data_set.is_recent_enough())

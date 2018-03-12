import unittest
import datetime

from pymongo import MongoClient
from hamcrest import assert_that, contains, has_entry

from backdrop.core.data_set import DataSet
from backdrop.core.storage.mongo import MongoStorageEngine
from backdrop.core.timeseries import WEEK
from backdrop.core.query import Query
from tests.support.test_helpers import d_tz

DATABASE_URL = 'mongodb://localhost:27017/backdrop_test'
DATA_SET = 'data_set_integration_test'


class TestDataSetIntegration(unittest.TestCase):

    def setUp(self):
        self.storage = MongoStorageEngine.create(DATABASE_URL)

        self.config = {
            'name': DATA_SET,
            'data_group': "group",
            'data_type': "type",
            'max_age_expected': 1000,
        }

        self.data_set = DataSet(self.storage, self.config)

        database = MongoClient(DATABASE_URL).get_database()
        self.mongo_collection = database[DATA_SET]

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

    def test_period_queries_get_sorted_by__week_start_at(self):
        self.setup__timestamp_data()
        query = Query.create(period=WEEK)
        result = self.data_set.execute_query(query)
        assert_that(result, contains(
            has_entry('_start_at', d_tz(2012, 12, 31)),
            has_entry('_start_at', d_tz(2013, 1, 28)),
            has_entry('_start_at', d_tz(2013, 2, 25))
        ))

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

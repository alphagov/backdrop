"""
Larger tests for the mongo storage engine.

This module includes integration tests and unit tests that require a significant
amount of setup and mocking. Small unit tests are in doctest format in the
module itself.
"""

from hamcrest import assert_that, is_, has_key
from nose.tools import assert_raises
from mock import Mock

import datetime

from pymongo.errors import AutoReconnect

from backdrop.core.storage.mongo import MongoStorageEngine, reconnecting_save, time_as_utc
from backdrop.core.data_set import DataSet

from .test_storage import BaseStorageTest

DATABASE_URL = 'mongodb://localhost:27017/backdrop_test'


class TestMongoStorageEngine(BaseStorageTest):
    def setup(self):
        self.engine = MongoStorageEngine.create(DATABASE_URL)

    def test_create_data_set(self):
        self.engine.create_data_set('should_have_index', 0)

        coll = self.engine._collection('should_have_index')
        indicies = coll.index_information()

        assert_that(indicies, has_key('_timestamp_-1'))

    def teardown(self):
        mongo_client = self.engine._mongo_client
        database_name = mongo_client.get_database().name
        mongo_client.drop_database(database_name)


class TestReconnectingSave(object):
    def test_reconnecting_save_retries(self):
        collection = Mock()
        collection.save.side_effect = [AutoReconnect, None]

        reconnecting_save(collection, 'record')

        assert_that(collection.save.call_count, is_(2))

    def test_reconnecting_save_fails_after_3_retries(self):
        collection = Mock()
        collection.save.side_effect = [AutoReconnect, AutoReconnect, AutoReconnect, None]

        assert_raises(AutoReconnect, reconnecting_save, collection, 'record')

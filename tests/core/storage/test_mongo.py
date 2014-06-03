"""
Larger tests for the mongo storage engine.

This module includes integration tests and unit tests that require a significant
amount of setup and mocking. Small unit tests are in doctest format in the
module itself.
"""

from hamcrest import assert_that, is_
from nose.tools import assert_raises
from mock import Mock

from pymongo.errors import AutoReconnect

from backdrop.core.storage.mongo import MongoStorageEngine, reconnecting_save

from .test_storage import BaseStorageTest


class TestMongoStorageEngine(BaseStorageTest):
    def setup(self):
        self.engine = MongoStorageEngine.create(
            ['localhost'], 27017, 'backdrop_test')

    def teardown(self):
        self.engine._mongo.drop_database('backdrop_test')


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

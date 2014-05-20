"""
Integration tests for the mongo storage engine.
Unit tests are in doctest format in the module itself.
"""
from hamcrest import assert_that, is_

from backdrop.core.storage.mongo import MongoStorageEngine


class TestMongoStorageEngine(object):
    def setup(self):
        self.engine = MongoStorageEngine.create(
            ['localhost'], 27017, 'backdrop_test')

    # ALIVE
    def test_alive_returns_true_if_mongo_is_up(self):
        assert_that(self.engine.alive(), is_(True))

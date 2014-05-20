"""
Integration tests for the mongo storage engine.
Unit tests are in doctest format in the module itself.
"""
from hamcrest import assert_that, is_, has_item, has_entries
from nose.tools import assert_raises

from pymongo.errors import CollectionInvalid

from backdrop.core.storage.mongo import MongoStorageEngine


class TestMongoStorageEngine(object):
    def setup(self):
        self.engine = MongoStorageEngine.create(
            ['localhost'], 27017, 'backdrop_test')
        self.mongo = self.engine._mongo
        self.db = self.mongo['backdrop_test']

    def teardown(self):
        self.mongo.drop_database('backdrop_test')

    # ALIVE
    def test_alive_returns_true_if_mongo_is_up(self):
        assert_that(self.engine.alive(), is_(True))

    # EXISTS
    def test_exists_returns_false_if_data_set_does_not_exist(self):
        assert_that(self.engine.dataset_exists('foo_bar'), is_(False))

    def test_exists_returns_true_if_data_set_exists(self):
        self.db.create_collection('foo_bar')

        assert_that(self.engine.dataset_exists('foo_bar'), is_(True))

    # CREATE
    def test_create_a_non_capped_collection(self):
        self.engine.create_dataset('foo_bar', 0)

        assert_that(self.db.collection_names(), has_item('foo_bar'))
        assert_that(self.db['foo_bar'].options(), has_entries(
            {'capped': False}))

    def test_create_a_capped_collection(self):
        self.engine.create_dataset('foo_bar', 100)

        assert_that(self.db.collection_names(), has_item('foo_bar'))
        assert_that(self.db['foo_bar'].options(), has_entries(
            {'capped': True, 'size': 100}))

    def test_create_fails_if_collection_already_exists(self):
        # TODO: reraise a backdrop exception
        self.engine.create_dataset('foo_bar', 0)

        assert_raises(CollectionInvalid,
                      self.engine.create_dataset, 'foo_bar', 0)

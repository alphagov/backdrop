"""
Larger tests for the mongo storage engine.

This module includes integration tests and unit tests that require a significant
amount of setup and mocking. Small unit tests are in doctest format in the
module itself.
"""
import datetime

from hamcrest import assert_that, is_, has_item, has_entries, is_not, \
    has_entry, instance_of, contains, only_contains
from nose.tools import assert_raises
from mock import Mock

from pymongo.errors import CollectionInvalid, AutoReconnect

from backdrop.core.storage.mongo import MongoStorageEngine, reconnecting_save
from backdrop.read.query import Query

from tests.support.test_helpers import d_tz


class TestMongoStorageEngine(object):
    def setup(self):
        self.engine = MongoStorageEngine.create(
            ['localhost'], 27017, 'backdrop_test')
        self.mongo = self.engine._mongo
        self.db = self.mongo['backdrop_test']

    def teardown(self):
        self.mongo.drop_database('backdrop_test')

    def _save(self, dataset_id, **kwargs):
        self.db[dataset_id].save(kwargs)

    def _save_all(self, dataset_id, *records):
        for record in records:
            self._save(dataset_id, **record)

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

    # DELETE
    def test_delete_a_dataset(self):
        self.engine.create_dataset('foo_bar', 0)

        self.engine.delete_dataset('foo_bar')

        assert_that(self.db.collection_names(), is_not(has_item('foo_bar')))

    def test_create_fails_if_collection_already_exists(self):
        # TODO: reraise a backdrop exception
        self.engine.create_dataset('foo_bar', 0)

        assert_raises(CollectionInvalid,
                      self.engine.create_dataset, 'foo_bar', 0)

    # GET LAST UPDATED
    def test_get_last_udpated(self):
        self._save('foo_bar', _id='first', _updated_at=d_tz(2013, 3, 1))
        self._save('foo_bar', _id='second', _updated_at=d_tz(2013, 9, 1))
        self._save('foo_bar', _id='third', _updated_at=d_tz(2013, 3, 1))

        assert_that(self.engine.get_last_updated('foo_bar'),
                    is_(d_tz(2013, 9, 1)))

    def test_returns_none_if_there_is_no_last_updated(self):
        assert_that(self.engine.get_last_updated('foo_bar'), is_(None))

    # EMPTY
    def test_empty_a_dataset(self):
        self._save('foo_bar', _id='first')
        self._save('foo_bar', _id='second')

        assert_that(self.db['foo_bar'].count(), is_(2))

        self.engine.empty('foo_bar')

        assert_that(self.db['foo_bar'].count(), is_(0))

    # SAVE
    def test_save_a_record(self):
        self.engine.save('foo_bar', {'_id': 'first'})

        assert_that(self.db['foo_bar'].count(), is_(1))

    def test_save_a_record_adds_an_updated_at(self):
        self.engine.save('foo_bar', {'_id': 'first'})

        assert_that(self.db['foo_bar'].find_one(),
                    has_entry('_updated_at', instance_of(datetime.datetime)))

    # QUERY
    def test_basic_query(self):
        self._save_all('foo_bar',
                       {'foo': 'bar'},
                       {'bar': 'foo'})

        results = self.engine.query('foo_bar', Query.create())

        assert_that(results,
                    contains(
                        has_entries({'foo': 'bar'}),
                        has_entries({'bar': 'foo'})))

    def test_datetimes_are_converted_to_utc(self):
        self._save('foo_bar', _timestamp=datetime.datetime(2012, 12, 12))

        results = self.engine.query('foo_bar', Query.create())

        assert_that(results,
                    contains(
                        has_entry('_timestamp', d_tz(2012, 12, 12))))

    def test_basic_query_with_filter(self):
        self._save_all('foo_bar', {'foo': 'bar'}, {'bar': 'foo'})

        results = self.engine.query('foo_bar', Query.create(
            filter_by=[('foo', 'bar')]))

        assert_that(results,
                    only_contains(
                        has_entry('foo', 'bar')))

    def test_basic_query_with_time_limits(self):
        self._save_all('foo_bar',
            {'_timestamp': d_tz(2012, 12, 12)},
            {'_timestamp': d_tz(2012, 12, 14)},
            {'_timestamp': d_tz(2012, 12, 11)})

        # start at
        results = self.engine.query('foo_bar', Query.create(
            start_at=d_tz(2012, 12, 12, 13)))

        assert_that(results,
                    only_contains(
                        has_entry('_timestamp', d_tz(2012, 12, 14))))

        # end at
        results = self.engine.query('foo_bar', Query.create(
            end_at=d_tz(2012, 12, 11, 13)))

        assert_that(results,
                    only_contains(
                        has_entry('_timestamp', d_tz(2012, 12, 11))))

        # both
        results = self.engine.query('foo_bar', Query.create(
            start_at=d_tz(2012, 12, 11, 12),
            end_at=d_tz(2012, 12, 12, 12)))

        assert_that(results,
                    only_contains(
                        has_entry('_timestamp', d_tz(2012, 12, 12))))


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

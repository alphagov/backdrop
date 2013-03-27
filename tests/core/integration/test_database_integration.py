import unittest
import datetime
from abc import ABCMeta
from hamcrest import *
from pymongo import MongoClient
from backdrop.core.database import Repository, GroupingError, \
    InvalidSortError
from tests.support.test_helpers import d, d_tz

HOST = 'localhost'
PORT = 27017
DB_NAME = 'performance_platform_test'
BUCKET = 'test_repository_integration'


class RepositoryIntegrationTest(unittest.TestCase):
    __metaclass__ = ABCMeta

    def setUp(self):
        self.repo = Repository(MongoClient(HOST, PORT)[DB_NAME][BUCKET])
        self.mongo_collection = MongoClient(HOST, PORT)[DB_NAME][BUCKET]

    def tearDown(self):
        self.mongo_collection.drop()


class TestRepositoryIntegration(RepositoryIntegrationTest):
    def test_save(self):
        thing_to_save = {'name': 'test_document'}
        another_thing_to_save = {'name': '2nd_test_document'}

        self.repo.save(thing_to_save)
        self.repo.save(another_thing_to_save)

        results = self.mongo_collection.find()
        assert_that(results, has_item(thing_to_save))
        assert_that(results, has_item(another_thing_to_save))

    def test_save_updates_document_with_id(self):
        a_document = {"_id": "event1", "title": "I'm an event"}
        updated_document = {"_id": "event1", "title": "I'm another event"}

        self.repo.save(a_document)
        self.repo.save(updated_document)

        saved_documents = self.mongo_collection.find()

        assert_that( saved_documents, only_contains(updated_document) )

    def test_find(self):
        self.mongo_collection.save({"name": "George", "plays": "guitar"})
        self.mongo_collection.save({"name": "John", "plays": "guitar"})
        self.mongo_collection.save({"name": "Paul", "plays": "bass"})
        self.mongo_collection.save({"name": "Ringo", "plays": "drums"})

        results = self.repo.find({"plays": "guitar"})

        assert_that(results, only_contains(
            has_entries({"name": "George", "plays": "guitar"}),
            has_entries({"name": "John", "plays": "guitar"}),
        ))

    def test_group(self):
        self.mongo_collection.save({"name": "George", "plays": "guitar"})
        self.mongo_collection.save({"name": "John", "plays": "guitar"})
        self.mongo_collection.save({"name": "Paul", "plays": "bass"})
        self.mongo_collection.save({"name": "Ringo", "plays": "drums"})

        results = self.repo.group("plays", {})

        assert_that(results, only_contains(
            has_entries({"plays": "guitar", "_count": 2}),
            has_entries({"plays": "bass", "_count": 1}),
            has_entries({"plays": "drums", "_count": 1})
        ))

    def test_group_with_query(self):
        self.mongo_collection.save({"value": '1', "suite": "hearts"})
        self.mongo_collection.save({"value": '1', "suite": "diamonds"})
        self.mongo_collection.save({"value": '1', "suite": "clubs"})
        self.mongo_collection.save({"value": 'K', "suite": "hearts"})
        self.mongo_collection.save({"value": 'K', "suite": "diamonds"})

        results = self.repo.group("value", {"suite": "diamonds"})

        assert_that(results, only_contains(
            {"value": "1", "_count": 1},
            {"value": "K", "_count": 1}
        ))

    def test_key1_is_pulled_to_the_top_of_outer_group(self):
        self.mongo_collection.save({
            "_week_start_at": d_tz(2013, 3, 17, 0, 0, 0),
            "a": 1,
            "b": 2
        })
        self.mongo_collection.save({
            "_week_start_at": d_tz(2013, 3, 24, 0, 0, 0),
            "a": 1,
            "b": 2
        })

        result = self.repo.multi_group("_week_start_at", "a", {})
        assert_that(result, has_item(has_entry(
            "_week_start_at", datetime.datetime(2013, 3, 17, 0, 0, 0)
        )))
        assert_that(result, has_item(has_entry(
            "_week_start_at", datetime.datetime(2013, 3, 24, 0, 0, 0)
        )))

    def test_should_use_second_key_for_inner_group_name(self):
        self.mongo_collection.save({
            "_week_start_at": d_tz(2013, 3, 17, 0, 0, 0),
            "a": 1,
            "b": 2
        })
        self.mongo_collection.save({
            "_week_start_at": d_tz(2013, 3, 24, 0, 0, 0),
            "a": 1,
            "b": 2
        })

        result = self.repo.multi_group("_week_start_at", "a", {})
        assert_that(result, has_item(has_entry(
            "a", {1: {"_count": 1}}
        )))

    def test_count_of_outer_elements_should_be_added(self):
        self.mongo_collection.save({
            "_week_start_at": d_tz(2013, 3, 17, 0, 0, 0),
            "a": 1,
            "b": 2
        })
        self.mongo_collection.save({
            "_week_start_at": d_tz(2013, 3, 24, 0, 0, 0),
            "a": 1,
            "b": 2
        })

        result = self.repo.multi_group("_week_start_at", "a", {})
        assert_that(result, has_item(has_entry(
            "_count", 1
        )))

    def test_grouping_by_multiple_keys(self):
        self.mongo_collection.save({"value": '1',
                                    "suite": "hearts",
                                    "hand": 1})
        self.mongo_collection.save({"value": '1',
                                    "suite": "diamonds",
                                    "hand": 1})
        self.mongo_collection.save({"value": '1',
                                    "suite": "clubs",
                                    "hand": 1})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "hearts",
                                    "hand": 1})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "diamonds",
                                    "hand": 1})

        self.mongo_collection.save({"value": '1',
                                    "suite": "hearts",
                                    "hand": 2})
        self.mongo_collection.save({"value": '1',
                                    "suite": "diamonds",
                                    "hand": 2})
        self.mongo_collection.save({"value": '1',
                                    "suite": "clubs",
                                    "hand": 2})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "hearts",
                                    "hand": 2})
        self.mongo_collection.save({"value": 'Q',
                                    "suite": "diamonds",
                                    "hand": 2})

        result = self.repo.multi_group("value", "suite", {})

        assert_that(result, has_items(
            {
                "value": '1',
                "_count": 6,
                "_group_count": 3,
                "suite": {
                    "hearts": {
                        "_count": 2.0
                    },
                    "clubs": {
                        "_count": 2.0
                    },
                    "diamonds": {
                        "_count": 2.0
                    }
                    }
            },
            {
                "value": 'Q',
                "_count": 1,
                "_group_count": 1,
                "suite": {
                    "diamonds": {
                        "_count": 1.0
                    }
                }
            },
            {
                "value": 'K',
                "_count": 3,
                "_group_count": 2,
                "suite": {
                    "hearts": {
                        "_count": 2.0
                    },
                    "diamonds": {
                        "_count": 1.0
                    }
                }
            }
        ))

    def test_grouping_on_non_existent_keys(self):
        self.mongo_collection.save({"value": '1',
                                    "suite": "hearts",
                                    "hand": 1})
        self.mongo_collection.save({"value": '1',
                                    "suite": "diamonds",
                                    "hand": 1})
        self.mongo_collection.save({"value": '1',
                                    "suite": "clubs",
                                    "hand": 1})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "hearts",
                                    "hand": 1})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "diamonds",
                                    "hand": 1})

        result1 = self.repo.group('wibble', {})

        assert_that(result1, is_([]))

    def test_multi_grouping_on_non_existent_keys(self):
        self.mongo_collection.save({"value": '1',
                                    "suite": "hearts",
                                    "hand": 1})
        self.mongo_collection.save({"value": '1',
                                    "suite": "diamonds",
                                    "hand": 1})
        self.mongo_collection.save({"value": '1',
                                    "suite": "clubs",
                                    "hand": 1})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "hearts",
                                    "hand": 1})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "diamonds",
                                    "hand": 1})

        self.mongo_collection.save({"value": '1',
                                    "suite": "hearts",
                                    "hand": 2})
        self.mongo_collection.save({"value": '1',
                                    "suite": "diamonds",
                                    "hand": 2})
        self.mongo_collection.save({"value": '1',
                                    "suite": "clubs",
                                    "hand": 2})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "hearts",
                                    "hand": 2})
        self.mongo_collection.save({"value": 'Q',
                                    "suite": "diamonds",
                                    "hand": 2})

        result1 = self.repo.multi_group("wibble", "value", {})
        result2 = self.repo.multi_group("value", "wibble", {})

        assert_that(result1, is_([]))
        assert_that(result2, is_([]))

    def test_multi_grouping_on_empty_collection_returns_empty_list(self):
        assert_that(list(self.mongo_collection.find({})), is_([]))
        assert_that(self.repo.multi_group('a', 'b', {}), is_([]))

    def test_multi_grouping_on_same_key_raises_exception(self):
        self.mongo_collection.save({"value": '1',
                                    "suite": "hearts",
                                    "hand": 1})
        self.mongo_collection.save({"value": '1',
                                    "suite": "diamonds",
                                    "hand": 1})
        self.mongo_collection.save({"value": '1',
                                    "suite": "clubs",
                                    "hand": 1})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "hearts",
                                    "hand": 1})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "diamonds",
                                    "hand": 1})

        self.mongo_collection.save({"value": '1',
                                    "suite": "hearts",
                                    "hand": 2})
        self.mongo_collection.save({"value": '1',
                                    "suite": "diamonds",
                                    "hand": 2})
        self.mongo_collection.save({"value": '1',
                                    "suite": "clubs",
                                    "hand": 2})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "hearts",
                                    "hand": 2})
        self.mongo_collection.save({"value": 'Q',
                                    "suite": "diamonds",
                                    "hand": 2})

        try:
            self.repo.multi_group("suite", "suite", {})
            #fail if exception not raised
            assert_that(False)
        except GroupingError, e:
            assert_that(str(e), is_("Cannot group on two equal keys"))


class TestRepositoryIntegrationSorting(RepositoryIntegrationTest):
    def setUp(self):
        super(TestRepositoryIntegrationSorting, self).setUp()

    def tearDown(self):
        super(TestRepositoryIntegrationSorting, self).tearDown()

    def setup_numeric_values(self):
        self.mongo_collection.save({"value": 6})
        self.mongo_collection.save({"value": 2})
        self.mongo_collection.save({"value": 9})

    def setup_playing_cards(self):
        self.mongo_collection.save({"suite": "clubs"})
        self.mongo_collection.save({"suite": "hearts"})
        self.mongo_collection.save({"suite": "clubs"})
        self.mongo_collection.save({"suite": "diamonds"})
        self.mongo_collection.save({"suite": "clubs"})
        self.mongo_collection.save({"suite": "hearts"})

    def test_sorted_query_default_sort_order(self):
        self.mongo_collection.save({"_timestamp": d(2012, 12, 13)})
        self.mongo_collection.save({"_timestamp": d(2012, 12, 12)})
        self.mongo_collection.save({"_timestamp": d(2012, 12, 16)})

        result = self.repo.find({})

        assert_that(list(result), contains(
            has_entry("_timestamp", d(2012, 12, 12)),
            has_entry("_timestamp", d(2012, 12, 13)),
            has_entry("_timestamp", d(2012, 12, 16)),
        ))

    def test_sorted_query_ascending(self):
        self.mongo_collection.save({"value": 6})
        self.mongo_collection.save({"value": 2})
        self.mongo_collection.save({"value": 9})

        result = self.repo.find({}, sort=["value", "ascending"])

        assert_that(list(result), contains(
            has_entry('value', 2),
            has_entry('value', 6),
            has_entry('value', 9),
        ))

    def test_sorted_query_descending(self):
        self.setup_numeric_values()

        result = self.repo.find({}, sort=["value", "descending"])

        assert_that(list(result), contains(
            has_entry('value', 9),
            has_entry('value', 6),
            has_entry('value', 2),
        ))

    def test_sorted_query_nonsense(self):
        self.setup_numeric_values()

        self.assertRaises(
            InvalidSortError,
            self.repo.find,
            {}, sort=["value", "coolness"])

    def test_sorted_query_not_enough_args(self):
        self.setup_numeric_values()

        self.assertRaises(
            InvalidSortError,
            self.repo.find,
            {}, sort=["value"])

    def test_sorted_query_with_alphanumeric(self):
        self.mongo_collection.save({'val': 'a'})
        self.mongo_collection.save({'val': 'b'})
        self.mongo_collection.save({'val': 'c'})

        result = self.repo.find({}, sort=['val', 'descending'])
        assert_that(list(result), contains(
            has_entry('val', 'c'),
            has_entry('val', 'b'),
            has_entry('val', 'a')
        ))

    def test_sorted_group_ascending(self):
        self.setup_playing_cards()

        result = self.repo.group("suite", {}, sort=["suite", "ascending"])

        assert_that(list(result), contains(
            has_entry("suite", "clubs"),
            has_entry("suite", "diamonds"),
            has_entry("suite", "hearts")
        ))

    def test_sorted_group_descending(self):
        self.setup_playing_cards()

        result = self.repo.group("suite", {}, sort=["suite", "descending"])

        assert_that(list(result), contains(
            has_entry("suite", "hearts"),
            has_entry("suite", "diamonds"),
            has_entry("suite", "clubs")
        ))

    def test_sorted_group_nonsense(self):
        self.setup_playing_cards()

        self.assertRaises(
            InvalidSortError,
            self.repo.group,
            "suite", {}, sort=["suite", "coolness"])

    def test_sorted_group_not_enough_args(self):
        self.setup_playing_cards()

        self.assertRaises(
            InvalidSortError,
            self.repo.group,
            "suite", {}, sort=["suite"])

    def test_sorted_group_by_count(self):
        self.setup_playing_cards()

        result = self.repo.group("suite", {}, sort=["_count", "ascending"])

        assert_that(list(result), contains(
            has_entry("suite", "diamonds"),
            has_entry("suite", "hearts"),
            has_entry("suite", "clubs")
        ))

    def test_sorted_group_by_nonexistent_key(self):
        self.setup_playing_cards()

        self.assertRaises(
            InvalidSortError,
            self.repo.group,
            "suite", {}, sort=["bleh", "ascending"]
        )

    def test_periodic_group_is_sorted_by__week_start_at(self):
        self.mongo_collection.save({"_week_start_at": d(2013, 3, 17),
                                    'val': 1})
        self.mongo_collection.save({"_week_start_at": d(2013, 3, 24),
                                    'val': 7})

        result = self.repo.multi_group('_week_start_at', 'val', {})

        assert_that(list(result), contains(
            has_entry('_week_start_at', d(2013, 3, 17)),
            has_entry('_week_start_at', d(2013, 3, 24)),
        ))

    def test_query_with_limit(self):
        self.mongo_collection.save({"value": 6})
        self.mongo_collection.save({"value": 2})
        self.mongo_collection.save({"value": 9})

        result = self.repo.find({}, limit=2)

        assert_that(result.count(with_limit_and_skip=True), is_(2))

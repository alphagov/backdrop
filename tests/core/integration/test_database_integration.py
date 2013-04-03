import pprint
import unittest
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


class TestRepositoryIntegration_Grouping(RepositoryIntegrationTest):
    def setUp(self):
        super(TestRepositoryIntegration_Grouping, self).setUp()
        people = ["Jack", "Jill", "John", "Jane"]
        places = ["Kettering", "Kew", "Kennington", "Kingston"]
        hair = ["red", "dark", "blond"]
        times = [d_tz(2013, 3, 11), d_tz(2013, 3, 18), d_tz(2013, 3, 25)]

        self._save_location("Jack", "Kettering", "red", d_tz(2013, 3, 11))
        self._save_location("Jill", "Kennington", "blond", d_tz(2013, 3, 25))
        self._save_location("John", "Kettering", "blond", d_tz(2013, 3, 18))
        self._save_location("John", "Kettering", "dark", d_tz(2013, 3, 18))
        self._save_location("John", "Kennington", "dark", d_tz(2013, 3, 11))
        self._save_location("Jane", "Kingston", "red", d_tz(2013, 3, 18))

    def _save_location(self, person, place, hair, time):
        self.mongo_collection.save({
            "person": person,
            "place": place,
            "hair": hair,
            "_week_start_at": time
        })

    def tearDown(self):
        super(TestRepositoryIntegration_Grouping, self).tearDown()

    def test_group(self):
        results = self.repo.group("place", {})

        assert_that(results, only_contains(
            has_entries({"place": "Kettering", "_count": 3}),
            has_entries({"place": "Kennington", "_count": 2}),
            has_entries({"place": "Kingston", "_count": 1})
        ))

    def test_group_with_query(self):
        results = self.repo.group("place", {"person": "John"})

        assert_that(results, only_contains(
            {"place": "Kettering", "_count": 2},
            {"place": "Kennington", "_count": 1}
        ))

    def test_key1_is_pulled_to_the_top_of_outer_group(self):
        results = self.repo.multi_group("_week_start_at", "person", {})

        assert_that(results, has_item(has_entry(
            "_week_start_at", d(2013, 3, 11)
        )))
        assert_that(results, has_item(has_entry(
            "_week_start_at", d(2013, 3, 25)
        )))

    def test_should_use_second_key_for_inner_group_name(self):
        results = self.repo.multi_group("_week_start_at", "person", {})

        assert_that(results, has_item(has_entry(
            "_subgroup", has_item(has_entry("person", "Jill"))
        )))

    def test_count_of_outer_elements_should_be_added(self):
        results = self.repo.multi_group("_week_start_at", "person", {})

        assert_that(results, has_item(has_entry(
            "_count", 1
        )))

    def test_grouping_by_multiple_keys(self):
        results = self.repo.multi_group("person", "place", {})

        assert_that(results, has_item({
            "person": "Jack",
            "_count": 1,
            "_group_count": 1,
            "_subgroup": [
                { "place": "Kettering", "_count": 1 }
            ]
        }))
        assert_that(results, has_item({
            "person": "Jill",
            "_count": 1,
            "_group_count": 1,
            "_subgroup": [
                { "place": "Kennington", "_count": 1 }
            ]
        }))
        assert_that(results, has_item({
            "person": "John",
            "_count": 3,
            "_group_count": 2,
            "_subgroup": [
                { "place": "Kennington", "_count": 1 },
                { "place": "Kettering", "_count": 2 },
            ]
        }))

    def test_grouping_with_collect(self):
        results = self.repo.group("person", {}, None, None, ["place"])

        assert_that(results, has_item(has_entries({
            "person": "John",
            "place": ["Kettering", "Kennington"]
        })))

    def test_grouping_with_collect(self):
        results = self.repo.group("place", {}, None, None, ["person"])

        assert_that(results, has_item(has_entries({
            "place": "Kettering",
            "person": ["Jack", "John"]
        })))

    def test_grouping_with_collect_two_fields(self):
        results = self.repo.group("place", {}, None, None, ["person", "hair"])

        assert_that(results, has_item(has_entries({
            "place": "Kettering",
            "person": ["Jack", "John"],
            "hair": ["blond", "dark", "red"]
        })))

    def test_grouping_on_non_existent_keys(self):
        results = self.repo.group("wibble", {})

        assert_that(results, is_([]))

    def test_multi_grouping_on_non_existent_keys(self):
        result1 = self.repo.multi_group("wibble", "wobble", {})
        result2 = self.repo.multi_group("wibble", "person", {})
        result3 = self.repo.multi_group("person", "wibble", {})

        assert_that(result1, is_([]))
        assert_that(result2, is_([]))
        assert_that(result3, is_([]))

    def test_multi_grouping_on_empty_collection_returns_empty_list(self):
        self.mongo_collection.drop()
        assert_that(list(self.mongo_collection.find({})), is_([]))
        assert_that(self.repo.multi_group('a', 'b', {}), is_([]))

    def test_multi_grouping_on_same_key_raises_exception(self):
        self.assertRaises(GroupingError, self.repo.multi_group,
                          "person", "person", {})

    def test_multi_group_is_sorted_by_inner_key(self):
        results = self.repo.multi_group("person", "_week_start_at", {})

        assert_that(results, has_item(has_entries({
            "person": "John",
            "_subgroup": contains(
                has_entry("_week_start_at", d(2013, 3, 11)),
                has_entry("_week_start_at", d(2013, 3, 18)),
            )
        })))

    def test_sorted_multi_group_query_ascending(self):
        results = self.repo.multi_group("person", "_week_start_at", {},
                                        sort=["_count", "ascending"])

        assert_that(results, contains(
            has_entry("_count", 1),
            has_entry("_count", 1),
            has_entry("_count", 1),
            has_entry("_count", 3),
        ))

    def test_sorted_multi_group_query_descending(self):
        results = self.repo.multi_group("person", "_week_start_at", {},
                                        sort=["_count", "descending"])

        assert_that(results, contains(
            has_entry("_count", 3),
            has_entry("_count", 1),
            has_entry("_count", 1),
            has_entry("_count", 1),
        ))

    def test_sorted_multi_group_query_ascending_with_limit(self):
        results = self.repo.multi_group(
            "person",
            "_week_start_at",
            {},
            sort=["_count", "ascending"],
            limit=2
        )

        assert_that(results, contains(
            has_entry("_count", 1),
            has_entry("_count", 1),
        ))

    def test_sorted_multi_group_query_descending_with_limit(self):
        results = self.repo.multi_group(
            "person",
            "_week_start_at",
            {},
            sort=["_count", "descending"],
            limit=2
        )

        assert_that(results, contains(
            has_entry("_count", 3),
            has_entry("_count", 1),
        ))

    def test_multi_group_with_collect(self):
        results = self.repo.multi_group(
            "place",
            "_week_start_at",
            {},
            collect=["person"]
        )

        assert_that(results, has_item(has_entries({
            "place": "Kettering",
            "person": ["Jack", "John"]
        })))


class TestRepositoryIntegration_Sorting(RepositoryIntegrationTest):
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

    def test_sorted_group_by_with_limit(self):
        self.setup_playing_cards()

        result = self.repo.group(
            "suite", {}, sort=["_count", "ascending"], limit=1)

        assert_that(list(result), contains(
            has_entry("suite", "diamonds")
        ))

    def test_query_with_limit(self):
        self.mongo_collection.save({"value": 6})
        self.mongo_collection.save({"value": 2})
        self.mongo_collection.save({"value": 9})

        result = self.repo.find({}, limit=2)

        assert_that(result.count(with_limit_and_skip=True), is_(2))

    def test_query_with_limit_and_sort(self):
        self.mongo_collection.save({"value": 6})
        self.mongo_collection.save({"value": 2})
        self.mongo_collection.save({"value": 9})

        result = self.repo.find({}, sort=["value", "ascending"], limit=1)

        assert_that(result.count(with_limit_and_skip=True), is_(1))
        assert_that(list(result)[0], has_entry('value', 2))

    def test_period_query_for_data_with_no__week_start_at(self):
        self.mongo_collection.save({
            "_week_start_at": d(2013, 4, 2, 0, 0, 0),
            "foo": "bar"
        })
        self.mongo_collection.save({
            "foo": "bar2"
        })

        result = self.repo.group('_week_start_at', {})

        assert_that(result, has_item(has_entry("_count", 1)))

    def test_multigroup_query_for_data_with_different_missing_fields(self):
        self.mongo_collection.save({
            "_week_start_at": d(2013, 4, 2, 0, 0, 0),
            "foo": "1",
        })
        self.mongo_collection.save({
            "foo": "12",
            "bar": "2"
        })

        result = self.repo.multi_group("_week_start_at", "bar", {})

        assert_that(result, is_([]))

    def test_multigroup_query_for_data_with_different_missing_fields(self):
        self.mongo_collection.save({
            "_week_start_at": d(2013, 4, 2, 0, 0, 0),
            "foo": "1",
        })
        self.mongo_collection.save({
            "foo": "12",
            "bar": "2"
        })
        self.mongo_collection.save({
            "_week_start_at": d(2013, 4, 2, 0, 0, 0),
            "foo": "12",
            "bar": "2"
        })

        result = self.repo.multi_group("_week_start_at", "bar", {},
                                       collect=["foo"])

        assert_that(result, has_item(has_entry("_count", 1)))
        assert_that(result, has_item(has_entry("_group_count", 1)))

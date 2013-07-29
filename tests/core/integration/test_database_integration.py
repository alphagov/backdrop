import unittest
from abc import ABCMeta

from hamcrest import *
from pymongo import MongoClient

from backdrop.core.database import Repository, GroupingError, \
    InvalidSortError, MongoDriver, Database
from backdrop.read.query import Query
from tests.support.test_helpers import d, d_tz

HOST = 'localhost'
PORT = 27017
DB_NAME = 'performance_platform_test'
BUCKET = 'test_repository_integration'


class TestMongoDriver(unittest.TestCase):
    def setUp(self):
        self.mongo_driver = MongoDriver(MongoClient(HOST, PORT)[DB_NAME][BUCKET])

        self.mongo_collection = MongoClient(HOST, PORT)[DB_NAME][BUCKET]
        self.mongo_collection.drop()

    def test_save(self):
        thing_to_save = {'name': 'test_document'}
        another_thing_to_save = {'name': '2nd_test_document'}

        self.mongo_driver.save(thing_to_save)
        self.mongo_driver.save(another_thing_to_save)

        results = self.mongo_collection.find()
        assert_that(results, has_item(thing_to_save))
        assert_that(results, has_item(another_thing_to_save))

    def test_save_updates_document_with_id(self):
        a_document = {"_id": "event1", "title": "I'm an event"}
        updated_document = {"_id": "event1", "title": "I'm another event"}

        self.mongo_driver.save(a_document)
        self.mongo_driver.save(updated_document)

        saved_documents = self.mongo_collection.find()

        assert_that(saved_documents, only_contains(updated_document))

    def test_find(self):
        self._setup_people()

        results = self.mongo_driver.find(query={"plays": "guitar"},
                                         sort=["name", "ascending"],
                                         limit=None)

        assert_that(results, contains(
            has_entries({"name": "George", "plays": "guitar"}),
            has_entries({"name": "John", "plays": "guitar"}),
        ))

    def test_find_sort_descending(self):
        self._setup_people()

        results = self.mongo_driver.find(query={"plays": "guitar"},
                                         sort=["name", "descending"],
                                         limit=None)

        assert_that(results, contains(
            has_entries({"name": "John", "plays": "guitar"}),
            has_entries({"name": "George", "plays": "guitar"}),
        ))

    def test_find_with_limit(self):
        self._setup_people()

        results = self.mongo_driver.find(query={"plays": {"$ne": "guitar"}},
                                         sort=["name", "descending"],
                                         limit=1)

        assert_that(results, contains(
            has_entries({"name": "Ringo", "plays": "drums"})
        ))

    def test_group(self):
        self._setup_musical_instruments()

        results = self.mongo_driver.group(keys=["type"], query={}, collect_fields=[])

        assert_that(results, contains_inanyorder(
            has_entries({"_count": is_(2), "type": "wind"}),
            has_entries({"_count": is_(3), "type": "string"})
        ))

    def test_group_with_query(self):
        self._setup_musical_instruments()

        results = self.mongo_driver.group(keys=["type"],
                                          query={"range": "high"},
                                          collect_fields=[])

        assert_that(results, contains_inanyorder(
            has_entries({"_count": is_(1), "type": "wind"}),
            has_entries({"_count": is_(2), "type": "string"})
        ))

    def test_group_and_collect_additional_properties(self):
        self._setup_musical_instruments()

        results = self.mongo_driver.group(keys=["type"], query={}, collect_fields=["range"])

        assert_that(results, contains(
            has_entries(
                {"_count": is_(2),
                 "type": "wind",
                 "range": ["high", "low"]}),
            has_entries(
                {"_count": is_(3),
                 "type": "string",
                 "range": ["high", "high", "low"]})
        ))

    def test_group_and_collect_with_hyphen_in_field_name(self):
        self.mongo_collection.save({"type": "foo", "this-name": "bar"})
        self.mongo_collection.save({"type": "foo", "this-name": "bar"})
        self.mongo_collection.save({"type": "bar", "this-name": "bar"})
        self.mongo_collection.save({"type": "bar", "this-name": "foo"})

        results = self.mongo_driver.group(keys=["type"], query={}, collect_fields=["this-name"])

        assert_that(results, contains(
            has_entries(
                {"_count": is_(2),
                 "type": "foo",
                 "this-name": ["bar", "bar"]}),
            has_entries(
                {"_count": is_(2),
                 "type": "bar",
                 "this-name": ["bar", "foo"]})
        ))

    def test_group_and_collect_with_injection_attempt(self):
        self.mongo_collection.save({"type": "foo", "this-name": "bar"})
        self.mongo_collection.save({"type": "foo", "this-name": "bar"})
        self.mongo_collection.save({"type": "bar", "this-name": "bar"})
        self.mongo_collection.save({"type": "bar", "this-name": "foo"})

        for collect_field in ["name']-foo", "name\\']-foo"]:
            results = self.mongo_driver.group(keys=["type"], query={}, collect_fields=[collect_field])

            assert_that(results, contains(
                has_entries(
                    {"_count": is_(2),
                     "type": "foo"}),
                has_entries(
                    {"_count": is_(2),
                     "type": "bar"})
            ))

    def test_group_and_collect_with_false_value(self):
        self.mongo_collection.save({"foo": "one", "bar": False})
        self.mongo_collection.save({"foo": "two", "bar": True})
        self.mongo_collection.save({"foo": "two", "bar": True})
        self.mongo_collection.save({"foo": "one", "bar": False})

        results = self.mongo_driver.group(["foo"], {}, ["bar"])

        assert_that(results, contains(
            has_entries({
                "bar": [False, False]
            }),
            has_entries({
                "bar": [True, True]
            })
        ))

    def test_group_without_keys(self):
        self._setup_people()

        results = self.mongo_driver.group(keys=[], query={}, collect_fields=[])

        assert_that(results, contains(
            has_entries({"_count": is_(4)}),
        ))

    # this responsibility does not belong here
    def test_group_ignores_documents_without_grouping_keys(self):
        self._setup_people()
        self.mongo_collection.save({"name": "Yoko"})

        results = self.mongo_driver.group(keys=["plays"], query={}, collect_fields=[])

        assert_that(results, contains(
            has_entries({"_count": is_(2), "plays": "guitar"}),
            has_entries({"_count": is_(1), "plays": "bass"}),
            has_entries({"_count": is_(1), "plays": "drums"}),
        ))

    def _setup_people(self):
        self.mongo_collection.save({"name": "George", "plays": "guitar"})
        self.mongo_collection.save({"name": "John", "plays": "guitar"})
        self.mongo_collection.save({"name": "Paul", "plays": "bass"})
        self.mongo_collection.save({"name": "Ringo", "plays": "drums"})

    def _setup_musical_instruments(self):
        self.mongo_collection.save(
            {"instrument": "flute", "type": "wind", "range": "high"})
        self.mongo_collection.save(
            {"instrument": "contrabassoon", "type": "wind", "range": "low"})
        self.mongo_collection.save(
            {"instrument": "violin", "type": "string", "range": "high"})
        self.mongo_collection.save(
            {"instrument": "viola", "type": "string", "range": "high"})
        self.mongo_collection.save(
            {"instrument": "cello", "type": "string", "range": "low"})


class RepositoryIntegrationTest(unittest.TestCase):
    __metaclass__ = ABCMeta

    def setUp(self):
        mongo = MongoDriver(MongoClient(HOST, PORT)[DB_NAME][BUCKET])
        self.repo = Repository(mongo)

        self.mongo_collection = MongoClient(HOST, PORT)[DB_NAME][BUCKET]
        self.mongo_collection.drop()


class TestRepositoryIntegration_Grouping(RepositoryIntegrationTest):
    def setUpPeopleLocationData(self):
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

    def test_group(self):
        self.setUpPeopleLocationData()

        results = self.repo.group("place", Query.create())

        assert_that(results, only_contains(
            has_entries({"place": "Kettering", "_count": 3}),
            has_entries({"place": "Kennington", "_count": 2}),
            has_entries({"place": "Kingston", "_count": 1})
        ))

    def test_group_with_query(self):
        self.setUpPeopleLocationData()

        results = self.repo.group("place",
                                  Query.create(filter_by= [["person", "John"]]))

        assert_that(results, only_contains(
            {"place": "Kettering", "_count": 2},
            {"place": "Kennington", "_count": 1}
        ))

    def test_key1_is_pulled_to_the_top_of_outer_group(self):
        self.setUpPeopleLocationData()

        results = self.repo.multi_group("_week_start_at", "person", Query.create())

        assert_that(results, has_item(has_entry(
            "_week_start_at", d(2013, 3, 11)
        )))
        assert_that(results, has_item(has_entry(
            "_week_start_at", d(2013, 3, 25)
        )))

    def test_should_use_second_key_for_inner_group_name(self):
        self.setUpPeopleLocationData()

        results = self.repo.multi_group("_week_start_at", "person", Query.create())

        assert_that(results, has_item(has_entry(
            "_subgroup", has_item(has_entry("person", "Jill"))
        )))

    def test_count_of_outer_elements_should_be_added(self):
        self.setUpPeopleLocationData()

        results = self.repo.multi_group("_week_start_at", "person", Query.create())

        assert_that(results, has_item(has_entry(
            "_count", 1
        )))

    def test_grouping_by_multiple_keys(self):
        self.setUpPeopleLocationData()

        results = self.repo.multi_group("person", "place", Query.create())

        assert_that(results, has_item({
            "person": "Jack",
            "_count": 1,
            "_group_count": 1,
            "_subgroup": [
                {"place": "Kettering", "_count": 1}
            ]
        }))
        assert_that(results, has_item({
            "person": "Jill",
            "_count": 1,
            "_group_count": 1,
            "_subgroup": [
                {"place": "Kennington", "_count": 1}
            ]
        }))
        assert_that(results, has_item({
            "person": "John",
            "_count": 3,
            "_group_count": 2,
            "_subgroup": [
                {"place": "Kennington", "_count": 1},
                {"place": "Kettering", "_count": 2},
            ]
        }))

    def test_grouping_with_collect(self):
        self.setUpPeopleLocationData()

        results = self.repo.group("person", Query.create(), None, None, [("place", "set")])

        assert_that(results, has_item(has_entries({
            "person": "John",
            "place:set": has_items("Kettering", "Kennington")
        })))

    def test_another_grouping_with_collect(self):
        self.setUpPeopleLocationData()

        results = self.repo.group("place", Query.create(), None, None, [("person", "set")])

        assert_that(results, has_item(has_entries({
            "place": "Kettering",
            "person:set": has_items("Jack", "John")
        })))

    def test_grouping_with_collect_two_fields(self):
        self.setUpPeopleLocationData()

        results = self.repo.group("place", Query.create(), None, None,
                                  [("person", "set"), ("hair", "set")])

        assert_that(results, has_item(has_entries({
            "place": "Kettering",
            "person:set": ["Jack", "John"],
            "hair:set": ["blond", "dark", "red"]
        })))

    def test_grouping_on_non_existent_keys(self):
        self.setUpPeopleLocationData()

        results = self.repo.group("wibble", Query.create())

        assert_that(results, is_([]))

    def test_multi_grouping_on_non_existent_keys(self):
        self.setUpPeopleLocationData()

        result1 = self.repo.multi_group("wibble", "wobble", Query.create())
        result2 = self.repo.multi_group("wibble", "person", Query.create())
        result3 = self.repo.multi_group("person", "wibble", Query.create())

        assert_that(result1, is_([]))
        assert_that(result2, is_([]))
        assert_that(result3, is_([]))

    def test_multi_grouping_on_empty_collection_returns_empty_list(self):
        assert_that(self.repo.multi_group('a', 'b', Query.create()), is_([]))

    def test_multi_grouping_on_same_key_raises_exception(self):
        self.assertRaises(GroupingError, self.repo.multi_group,
                          "person", "person", Query.create())

    def test_multi_group_is_sorted_by_inner_key(self):
        self.setUpPeopleLocationData()

        results = self.repo.multi_group("person", "_week_start_at", Query.create())

        assert_that(results, has_item(has_entries({
            "person": "John",
            "_subgroup": contains(
                has_entry("_week_start_at", d(2013, 3, 11)),
                has_entry("_week_start_at", d(2013, 3, 18)),
            )
        })))

    def test_sorted_multi_group_query_ascending(self):
        self.setUpPeopleLocationData()

        results = self.repo.multi_group("person", "_week_start_at", Query.create(),
                                        sort=["_count", "ascending"])

        assert_that(results, contains(
            has_entry("_count", 1),
            has_entry("_count", 1),
            has_entry("_count", 1),
            has_entry("_count", 3),
        ))

    def test_sorted_multi_group_query_descending(self):
        self.setUpPeopleLocationData()

        results = self.repo.multi_group("person", "_week_start_at", Query.create(),
                                        sort=["_count", "descending"])

        assert_that(results, contains(
            has_entry("_count", 3),
            has_entry("_count", 1),
            has_entry("_count", 1),
            has_entry("_count", 1),
        ))

    def test_sorted_multi_group_query_ascending_with_limit(self):
        self.setUpPeopleLocationData()

        results = self.repo.multi_group(
            "person",
            "_week_start_at",
            Query.create(),
            sort=["_count", "ascending"],
            limit=2
        )

        assert_that(results, contains(
            has_entry("_count", 1),
            has_entry("_count", 1),
        ))

    def test_sorted_multi_group_query_descending_with_limit(self):
        self.setUpPeopleLocationData()

        results = self.repo.multi_group(
            "person",
            "_week_start_at",
            Query.create(),
            sort=["_count", "descending"],
            limit=2
        )

        assert_that(results, contains(
            has_entry("_count", 3),
            has_entry("_count", 1),
        ))

    def test_multi_group_with_collect(self):
        self.setUpPeopleLocationData()

        results = self.repo.multi_group(
            "place",
            "_week_start_at",
            Query.create(),
            collect=[("person", "set")]
        )

        assert_that(results, has_item(has_entries({
            "place": "Kettering",
            "person:set": ["Jack", "John"]
        })))


class TestRepositoryIntegration_MultiGroupWithMissingFields(
        RepositoryIntegrationTest):
    def test_query_for_data_with_different_missing_fields_no_results(self):
        self.mongo_collection.save({
            "_week_start_at": d(2013, 4, 2, 0, 0, 0),
            "foo": "1",
        })
        self.mongo_collection.save({
            "foo": "12",
            "bar": "2"
        })

        result = self.repo.multi_group("_week_start_at", "bar", Query.create())

        assert_that(result, is_([]))

    def test_query_for_data_with_different_missing_fields_some_results(self):
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

        result = self.repo.multi_group("_week_start_at", "bar", Query.create())

        assert_that(result, has_item(has_entry("_count", 1)))
        assert_that(result, has_item(has_entry("_group_count", 1)))

    def test_query_for_data_with_different_missing_fields_with_filter(self):
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

        result = self.repo.multi_group("_week_start_at", "bar",
                                       Query.create(filter_by= [["bar", "2"]]))

        assert_that(result, has_item(has_entry("_count", 1)))
        assert_that(result, has_item(has_entry("_group_count", 1)))


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

        result = self.repo.find(Query.create())

        assert_that(list(result), contains(
            has_entry("_timestamp", d(2012, 12, 12)),
            has_entry("_timestamp", d(2012, 12, 13)),
            has_entry("_timestamp", d(2012, 12, 16)),
        ))

    def test_sorted_query_ascending(self):
        self.mongo_collection.save({"value": 6})
        self.mongo_collection.save({"value": 2})
        self.mongo_collection.save({"value": 9})

        result = self.repo.find(Query.create(), sort=["value", "ascending"])

        assert_that(list(result), contains(
            has_entry('value', 2),
            has_entry('value', 6),
            has_entry('value', 9),
        ))

    def test_sorted_query_descending(self):
        self.setup_numeric_values()

        result = self.repo.find(Query.create(), sort=["value", "descending"])

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
            Query.create(), sort=["value", "coolness"])

    def test_sorted_query_not_enough_args(self):
        self.setup_numeric_values()

        self.assertRaises(
            InvalidSortError,
            self.repo.find,
            Query.create(), sort=["value"])

    def test_sorted_query_with_alphanumeric(self):
        self.mongo_collection.save({'val': 'a'})
        self.mongo_collection.save({'val': 'b'})
        self.mongo_collection.save({'val': 'c'})

        result = self.repo.find(Query.create(), sort=['val', 'descending'])
        assert_that(list(result), contains(
            has_entry('val', 'c'),
            has_entry('val', 'b'),
            has_entry('val', 'a')
        ))

    def test_sorted_group_ascending(self):
        self.setup_playing_cards()

        result = self.repo.group("suite", Query.create(), sort=["suite", "ascending"])

        assert_that(list(result), contains(
            has_entry("suite", "clubs"),
            has_entry("suite", "diamonds"),
            has_entry("suite", "hearts")
        ))

    def test_sorted_group_descending(self):
        self.setup_playing_cards()

        result = self.repo.group("suite", Query.create(), sort=["suite", "descending"])

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
            "suite", Query.create(), sort=["suite", "coolness"])

    def test_sorted_group_not_enough_args(self):
        self.setup_playing_cards()

        self.assertRaises(
            InvalidSortError,
            self.repo.group,
            "suite", Query.create(), sort=["suite"])

    def test_sorted_group_by_count(self):
        self.setup_playing_cards()

        result = self.repo.group("suite", Query.create(), sort=["_count", "ascending"])

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
            "suite", Query.create(), sort=["bleh", "ascending"]
        )

    def test_sorted_group_by_with_limit(self):
        self.setup_playing_cards()

        result = self.repo.group(
            "suite", Query.create(), sort=["_count", "ascending"], limit=1)

        assert_that(list(result), contains(
            has_entry("suite", "diamonds")
        ))

    def test_query_with_limit(self):
        self.mongo_collection.save({"value": 6})
        self.mongo_collection.save({"value": 2})
        self.mongo_collection.save({"value": 9})

        result = self.repo.find(Query.create(), limit=2)

        assert_that(result.count(with_limit_and_skip=True), is_(2))

    def test_query_with_limit_and_sort(self):
        self.mongo_collection.save({"value": 6})
        self.mongo_collection.save({"value": 2})
        self.mongo_collection.save({"value": 9})

        result = self.repo.find(Query.create(), sort=["value", "ascending"], limit=1)

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

        result = self.repo.group('_week_start_at', Query.create())

        assert_that(result, has_item(has_entry("_count", 1)))


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database('localhost', 27017, 'backdrop_test')

    def test_alive(self):
        assert_that(self.db.alive(), is_(True))

    def test_getting_a_repository(self):
        repository = self.db.get_repository('my_bucket')
        assert_that(repository, instance_of(Repository))

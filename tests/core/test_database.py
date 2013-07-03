import unittest
from hamcrest import assert_that, is_
from mock import Mock, patch
from pymongo.errors import AutoReconnect
from backdrop.core import database
from backdrop.core.database import Repository, InvalidSortError, MongoDriver, apply_collection_method
from backdrop.read.query import Query
from tests.support.test_helpers import d_tz


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.collection = Mock()
        self.driver = MongoDriver(self.collection)

    def test_save_retries_on_auto_reconnect(self):
        self.collection.save.side_effect = [AutoReconnect, None]

        self.driver.save({})

        assert_that(self.collection.save.call_count, is_(2))

    def test_save_stops_retrying_after_3_attempts(self):
        self.collection.save.side_effect = AutoReconnect

        self.assertRaises(AutoReconnect, self.driver.save, {})

        assert_that(self.collection.save.call_count, is_(3))

    def test_save_only_calls_once_on_success(self):
        self.collection.save.return_value = None

        self.driver.save({})

        assert_that(self.collection.save.call_count, is_(1))


class NestedMergeTestCase(unittest.TestCase):
    def setUp(self):
        self.dictionaries = [
            {'a': 1, 'b': 2, 'c': 3},
            {'a': 1, 'b': 1, 'c': 3},
            {'a': 2, 'b': 1, 'c': 3}
        ]

    def test_nested_merge_merges_dictionaries(self):
        output = database.nested_merge(['a', 'b'], [], self.dictionaries)

        assert_that(output[0], is_({
            "a": 1,
            "_count": 0,
            "_group_count": 2,
            "_subgroup": [
                {"b": 1},
                {"b": 2},
            ],
        }))
        assert_that(output[1], is_({
            "a": 2,
            "_count": 0,
            "_group_count": 1,
            "_subgroup": [
                {"b": 1}
            ],
        }))

    def test_nested_merge_squashes_duplicates(self):
        output = database.nested_merge(['a'], [], self.dictionaries)
        assert_that(output, is_([
            {'a': 1},
            {'a': 2}
        ]))

    def test_nested_merge_collect_default(self):
        stub_dictionaries = [
            {'a': 1, 'b': [2], 'c': 3},
            {'a': 1, 'b': [1], 'c': 3},
            {'a': 2, 'b': [1], 'c': 3}
        ]
        output = database.nested_merge(['a'], [('b', 'default')], stub_dictionaries)
        assert_that(output, is_([
            {'a': 1, 'b:set': [1, 2], 'b': [1, 2]},
            {'a': 2, 'b:set': [1], 'b': [1]}
        ]))

    def test_nested_merge_collect_set(self):
        stub_dictionaries = [
            {'a': 1, 'b': [2], 'c': 3},
            {'a': 1, 'b': [1], 'c': 3},
            {'a': 2, 'b': [1], 'c': 3}
        ]
        output = database.nested_merge(['a'], [('b', 'set')], stub_dictionaries)
        assert_that(output, is_([
            {'a': 1, 'b:set': [1, 2]},
            {'a': 2, 'b:set': [1]}
        ]))

    def test_nested_merge_collect_sum(self):
        stub_dictionaries = [
            {'a': 1, 'b': [2]},
            {'a': 1, 'b': [1]},
            {'a': 2, 'b': [1]}
        ]
        output = database.nested_merge(['a'], [('b', 'sum')], stub_dictionaries)
        assert_that(output, is_([
            {'a': 1, 'b:sum': 3},
            {'a': 2, 'b:sum': 1}
        ]))


class TestApplyCollectionMethod(unittest.TestCase):
    def test_sum(self):
        data = [2, 5, 8]
        response = apply_collection_method(data, "sum")
        assert_that(response, is_(15))

    def test_count(self):
        data = ['Sheep', 'Elephant', 'Wolf', 'Dog']
        response = apply_collection_method(data, "count")
        assert_that(response, is_(4))

    def test_set(self):
        data = ['Badger', 'Badger', 'Badger', 'Snake']
        response = apply_collection_method(data, "set")
        assert_that(response, is_(['Badger', 'Snake']))

    def test_mean(self):
        data = [13, 19, 15, 2]
        response = apply_collection_method(data, "mean")
        assert_that(response, is_(12.25))

    def test_unknown_collection_method_raises_error(self):
        self.assertRaises(ValueError,
                          apply_collection_method, ['foo'], "unknown")


class TestRepository(unittest.TestCase):
    def setUp(self):
        self.mongo = Mock()
        self.repo = Repository(self.mongo)

    @patch('backdrop.core.timeutils.now')
    def test_save_document_adding_timestamps(self, now):
        now.return_value = d_tz(2013, 4, 9, 13, 32, 5)

        self.repo.save({"name": "Gummo"})

        self.mongo.save.assert_called_once_with({
            "name": "Gummo",
            "_updated_at": d_tz(2013, 4, 9, 13, 32, 5)
        })

    # =========================
    # Tests for repository.find
    # =========================
    def test_find(self):
        self.mongo.find.return_value = "a_cursor"

        results = self.repo.find(
            Query.create(filter_by=[["plays", "guitar"]]),
            sort= ["name", "ascending"])

        self.mongo.find.assert_called_once_with({"plays": "guitar"},
                                                ["name", "ascending"], None)
        assert_that(results, is_("a_cursor"))

    def test_find_with_descending_sort(self):
        self.mongo.find.return_value = "a_cursor"

        results = self.repo.find(
            Query.create(filter_by=[["plays", "guitar"]]),
            sort= ["name", "descending"])

        self.mongo.find.assert_called_once_with({"plays": "guitar"},
                                                ["name", "descending"], None)
        assert_that(results, is_("a_cursor"))

    def test_find_with_default_sorting(self):
        self.mongo.find.return_value = "a_cursor"

        results = self.repo.find(
            Query.create(filter_by=[["plays", "guitar"]]))

        self.mongo.find.assert_called_once_with({"plays": "guitar"},
                                                ["_timestamp", "ascending"],
                                                None)
        assert_that(results, is_("a_cursor"))

    def test_find_with_limit(self):
        self.mongo.find.return_value = "a_cursor"

        results = self.repo.find(
            Query.create(filter_by=[["plays", "guitar"]]), limit=10)

        self.mongo.find.assert_called_once_with({"plays": "guitar"},
                                                ["_timestamp", "ascending"],
                                                10)
        assert_that(results, is_("a_cursor"))

    def test_sort_raises_error_if_sort_does_not_have_two_elements(self):
        self.assertRaises(
            InvalidSortError,
            self.repo.find,
            Query.create(), ["a_key"]
        )

    def test_sort_raises_error_if_sort_direction_invalid(self):
        self.assertRaises(
            InvalidSortError,
            self.repo.find,
            Query.create(), ["a_key", "blah"]
        )

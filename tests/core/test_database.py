import unittest
from hamcrest import assert_that, is_
from mock import Mock, patch
from pymongo.errors import AutoReconnect
from backdrop.core.database import Repository, InvalidSortError, MongoDriver
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

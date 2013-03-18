import unittest
import datetime
from hamcrest import *
from mock import Mock, call
import pytz
from backdrop.core import storage
from backdrop.core.records import Record


def d(year, month, day, hour, minute, seconds):
    return datetime.datetime(year, month, day, hour, minute, seconds,
                             tzinfo=pytz.UTC)


class TestMongoIntegration(unittest.TestCase):
    def setUp(self):
        mock_repository = Mock()
        self.bucket = storage.Bucket(mock_repository)
        self.mock_repository = mock_repository
        self.mock_repository.find.return_value = []
        self.mock_repository.group.return_value = []

    def test_that_a_single_object_gets_stored(self):
        obj = Record({"name": "Gummo"})

        self.bucket.store(obj)

        self.mock_repository.save.assert_called_once_with({"name": "Gummo"})

    def test_that_a_list_of_objects_get_stored(self):
        my_objects = [
            {"name": "Groucho"},
            {"name": "Harpo"},
            {"name": "Chico"}
        ]

        my_records = [Record(obj) for obj in my_objects]

        self.bucket.store(my_records)

        self.mock_repository.save.assert_has_calls([
            call({'name': "Groucho"}),
            call({"name": "Harpo"}),
            call({"name": "Chico"})
        ])

    def test_filter_by_query(self):
        self.bucket.query(filter_by=[['name', 'Chico']])
        self.mock_repository.find.assert_called_once()

    def test_group_by_query(self):
        self.mock_repository.group.return_value = [
            {"name": "Max", "count": 3 },
            {"name": "Gareth", "count": 2 }
        ]

        query_result = self.bucket.query(group_by = "name")

        self.mock_repository.group.assert_called_once_with("name", {})

        assert_that(query_result,
                    has_item(has_entries({'Max': equal_to(3)})))
        assert_that(query_result,
                    has_item(has_entries({'Gareth': equal_to(2)})))

    def test_query_with_start_at(self):
        self.bucket.query(start_at = d(2013, 4, 1, 12, 0, 0))
        self.mock_repository.find.assert_called_with(
            {"_timestamp": {"$gte": d(2013, 4, 1, 12, 0, 0)}})

    def test_query_with_end_at(self):
        self.bucket.query(end_at = d(2013, 4, 1, 12, 0, 0))

        self.mock_repository.find.assert_called_with(
            {"_timestamp": {"$lt": d(2013, 4, 1, 12, 0, 0)}})

    def test_query_with_start_at_and__end_at(self):
        self.bucket.query(
            end_at = d(2013, 3, 1, 12, 0, 0),
            start_at = d(2013, 2, 1, 12, 0, 0)
        )

        self.mock_repository.find.assert_called_with({
            "_timestamp": {
                "$gte": d(2013, 2, 1, 12, 0, 0),
                "$lt": d(2013, 3, 1, 12, 0, 0)
            }
        })

    def test_week_query(self):
        self.mock_repository.group.return_value = [
            {"_week_start_at": d(2013, 1, 7, 0, 0, 0), "count": 3 },
            {"_week_start_at": d(2013, 1, 14, 0, 0, 0), "count": 1 },
        ]

        query_result = self.bucket.query(period='week')

        self.mock_repository.group.assert_called_once_with(
            "_week_start_at", {})

        assert_that(query_result, has_length(2))
        assert_that(query_result, has_item(has_entries({
            "_start_at": equal_to(d(2013, 1, 7, 0, 0, 0)),
            "_end_at": equal_to(d(2013, 1, 14, 0, 0, 0)),
            "count": equal_to(3)
        })))
        assert_that(query_result, has_item(has_entries({
            "_start_at": equal_to(d(2013, 1, 14, 0, 0, 0)),
            "_end_at": equal_to(d(2013, 1, 21, 0, 0, 0)),
            "count": equal_to(1)
        })))

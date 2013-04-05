import pprint
import unittest
import datetime
from hamcrest import *
from mock import Mock, call
import pytz
from backdrop.core import bucket
from backdrop.core.records import Record
from tests.support.test_helpers import d, d_tz


class TestBucket(unittest.TestCase):
    def setUp(self):
        mock_database = Mock()
        mock_repository = Mock()
        mock_database.get_repository.return_value = mock_repository
        self.bucket = bucket.Bucket(mock_database, 'test_bucket')
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
            {"name": "Max", "_count": 3 },
            {"name": "Gareth", "_count": 2 }
        ]

        query_result = self.bucket.query(group_by = "name")

        self.mock_repository.group.assert_called_once_with(
            "name", {}, None, None, [])

        assert_that(query_result,
                    has_item(has_entries({'name': equal_to('Max'),
                                          '_count': equal_to(3)})))
        assert_that(query_result,
                    has_item(has_entries({'name': equal_to('Gareth'),
                                          '_count': equal_to(2)})))

    def test_sorted_group_by_query(self):
        self.bucket.query(
            group_by="name",
            sort_by=["name", "ascending"]
        )

        self.mock_repository.group.assert_called_once_with(
            "name", {}, ["name", "ascending"], None, [])

    def test_sorted_group_by_query_with_limit(self):
        self.bucket.query(
            group_by="name",
            sort_by=["name", "ascending"],
            limit=100
        )

        self.mock_repository.group.assert_called_once_with(
            "name", {}, ["name", "ascending"], 100, [])

    def test_group_by_query_with_collect(self):
        self.bucket.query(
            group_by="name",
            sort_by=None,
            limit=None,
            collect=["key"]
        )

        self.mock_repository.group.assert_called_once_with(
            "name", {}, None, None, ["key"])

    def test_query_with_start_at(self):
        self.bucket.query(start_at = d(2013, 4, 1, 12, 0, 0))
        self.mock_repository.find.assert_called_with(
            {"_timestamp": {"$gte": d(2013, 4, 1, 12, 0, 0)}},
            sort=None, limit=None)

    def test_query_with_end_at(self):
        self.bucket.query(end_at = d(2013, 4, 1, 12, 0, 0))

        self.mock_repository.find.assert_called_with(
            {"_timestamp": {"$lt": d(2013, 4, 1, 12, 0, 0)}},
            sort=None, limit=None)

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
        }, sort=None, limit=None)

    def test_query_with_sort(self):
        self.bucket.query(
            sort_by=["keyname", "descending"]
        )

        self.mock_repository.find.assert_called_with(
            {}, sort=["keyname", "descending"], limit=None
        )

    def test_query_with_limit(self):
        self.bucket.query(limit=5)

        self.mock_repository.find.assert_called_with({}, sort=None, limit=5)

    def test_week_query(self):
        self.mock_repository.group.return_value = [
            {"_week_start_at": d(2013, 1, 7, 0, 0, 0), "_count": 3 },
            {"_week_start_at": d(2013, 1, 14, 0, 0, 0), "_count": 1 },
        ]

        query_result = self.bucket.query(period='week')

        self.mock_repository.group.assert_called_once_with(
            "_week_start_at", {}, limit=None)

        assert_that(query_result, has_length(2))
        assert_that(query_result, has_item(has_entries({
            "_start_at": equal_to(d_tz(2013, 1, 7, 0, 0, 0)),
            "_end_at": equal_to(d_tz(2013, 1, 14, 0, 0, 0)),
            "_count": equal_to(3)
        })))
        assert_that(query_result, has_item(has_entries({
            "_start_at": equal_to(d_tz(2013, 1, 14, 0, 0, 0)),
            "_end_at": equal_to(d_tz(2013, 1, 21, 0, 0, 0)),
            "_count": equal_to(1)
        })))

    def test_week_query_with_limit(self):
        self.mock_repository.group.return_value = []

        self.bucket.query(period='week', limit=1)

        self.mock_repository.group.assert_called_once_with(
            "_week_start_at", {}, limit=1)

    def test_period_query_fails_when_weeks_do_not_start_on_monday(self):
        self.mock_repository.group.return_value = [
            {"_week_start_at": d(2013, 1, 7, 0, 0, 0), "_count": 3 },
            {"_week_start_at": d(2013, 1, 8, 0, 0, 0), "_count": 1 },
        ]

        self.assertRaises(
            ValueError,
            self.bucket.query,
            period='week'
        )

    def test_week_and_group_query(self):
        self.mock_repository.multi_group.return_value = [
            {
                "some_group": "val1",
                "_count": 6,
                "_group_count": 2,
                "_subgroup": [
                    {
                        "_week_start_at": d(2013, 1, 7, 0, 0, 0),
                        "_count": 1
                    },
                    {
                        "_week_start_at": d(2013, 1, 14, 0, 0, 0),
                        "_count": 5
                    }
                ]
            },
            {
                "some_group": "val2",
                "_count": 8,
                "_group_count": 2,
                "_subgroup": [
                    {
                        "_week_start_at": d(2013, 1, 7, 0, 0, 0),
                        "_count": 2
                    },
                    {
                        "_week_start_at": d(2013, 1, 14, 0, 0, 0),
                        "_count": 6
                    }
                ]
            }
        ]
        query_result = self.bucket.query(period="week", group_by="some_group")
        assert_that(query_result, has_length(2))
        assert_that(query_result, has_item(has_entries({
            "values": has_item({
                "_start_at": d_tz(2013, 1, 7, 0, 0, 0),
                "_end_at": d_tz(2013, 1, 14, 0, 0, 0),
                "_count": 1
            }),
            "some_group": "val1"
        })))
        assert_that(query_result, has_item(has_entries({
            "values": has_item({
                "_start_at": d_tz(2013, 1, 14, 0, 0, 0),
                "_end_at": d_tz(2013, 1, 21, 0, 0, 0),
                "_count": 5
            }),
            "some_group": "val1"
        })))
        assert_that(query_result, has_item(has_entries({
            "values": has_item({
                "_start_at": d_tz(2013, 1, 7, 0, 0, 0),
                "_end_at": d_tz(2013, 1, 14, 0, 0, 0),
                "_count": 2
            }),
            "some_group": "val2"
        })))
        assert_that(query_result, has_item(has_entries({
            "values": has_item({
                "_start_at": d_tz(2013, 1, 14, 0, 0, 0),
                "_end_at": d_tz(2013, 1, 21, 0, 0, 0),
                "_count": 6
            }),
            "some_group": "val2"
        })))

    def test_period_group_query_adds_missing_periods_in_correct_order(self):
        self.mock_repository.multi_group.return_value = [
            {
                "some_group": "val1",
                "_count": 6,
                "_group_count": 2,
                "_subgroup": [
                    {
                        "_week_start_at": d(2013, 1, 7, 0, 0, 0),
                        "_count": 1
                    }
                ]
            },
            {
                "some_group": "val2",
                "_count": 8,
                "_group_count": 2,
                "_subgroup": [
                    {
                        "_week_start_at": d(2013, 1, 21, 0, 0, 0),
                        "_count": 1
                    }
                ]
            }
        ]
        query_result = self.bucket.query(period="week", group_by="some_group")
        assert_that(query_result, has_item(has_entries({
            "values": has_item({
                "_start_at": d_tz(2013, 1, 21, 0, 0, 0),
                "_end_at": d_tz(2013, 1, 28, 0, 0, 0),
                "_count": 0
            }),
            "some_group": "val1"
        })))
        assert_that(query_result, has_item(has_entries({
            "values": contains(
                has_entry("_start_at", d_tz(2013, 1, 7, 0, 0, 0)),
                has_entry("_start_at", d_tz(2013, 1, 14, 0, 0, 0)),
                has_entry("_start_at", d_tz(2013, 1, 21, 0, 0, 0))
            ),
            "some_group": "val2"
        })))

    def test_sorted_week_and_group_query(self):
        self.mock_repository.multi_group.return_value = [
            {
                "some_group": "val1",
                "_count": 6,
                "_group_count": 2,
                "_subgroup": [
                    {
                        "_week_start_at": d(2013, 1, 7, 0, 0, 0),
                        "_count": 1
                    },
                    {
                        "_week_start_at": d(2013, 1, 14, 0, 0, 0),
                        "_count": 5
                    }
                ]
            },
            {
                "some_group": "val2",
                "_count": 8,
                "_group_count": 2,
                "_subgroup": [
                    {
                        "_week_start_at": d(2013, 1, 7, 0, 0, 0),
                        "_count": 2
                    },
                    {
                        "_week_start_at": d(2013, 1, 14, 0, 0, 0),
                        "_count": 6
                    }
                ]
            },
        ]

        self.bucket.query(
            period="week",
            group_by="some_group",
            sort_by=["_count", "descending"]
        )

        self.mock_repository.multi_group.assert_called_with(
            "some_group",
            "_week_start_at",
            {},
            sort=["_count", "descending"],
            limit=None,
            collect=[]
        )

    def test_sorted_week_and_group_query_with_limit(self):
        self.mock_repository.multi_group.return_value = [
            {
                "some_group": "val1",
                "_count": 6,
                "_group_count": 2,
                "_subgroup": [
                    {
                        "_week_start_at": d(2013, 1, 7, 0, 0, 0),
                        "_count": 1
                    },
                    {
                        "_week_start_at": d(2013, 1, 14, 0, 0, 0),
                        "_count": 5
                    }
                ]
            }
        ]

        self.bucket.query(
            period="week",
            group_by="some_group",
            sort_by=["_count", "descending"],
            limit=1,
            collect=[]
        )

        self.mock_repository.multi_group.assert_called_with(
            "some_group",
            "_week_start_at",
            {},
            sort=["_count", "descending"],
            limit=1,
            collect=[])

    def test_period_group_query_fails_when_weeks_do_not_start_on_monday(self):
        multi_group_results = [
            {
                "is": "Monday",
                "_subgroup": [
                    {"_week_start_at": d(2013, 4, 1), "_count": 1}
                ]
            },
            {
                "is": "also Monday",
                "_subgroup": [
                    {"_week_start_at": d(2013, 4, 8), "_count": 1}
                ]
            },
            {
                "is": "Tuesday",
                "_subgroup": [
                    {"_week_start_at": d(2013, 4, 9), "_count": 1}
                ]
            },
        ]

        self.mock_repository.multi_group.return_value = \
            multi_group_results

        try:
            self.bucket.query(period='week', group_by='d')
            assert_that(False)
        except ValueError as e:
            assert_that(str(e), is_(
                "Weeks MUST start on Monday. Corrupt Data: 2013-04-09 00:00:00"
            ))

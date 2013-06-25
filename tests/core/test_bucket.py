from base64 import b64encode
import unittest
from hamcrest import *
from mock import Mock, call
from nose.tools import raises
from backdrop.core import bucket
from backdrop.core.bucket import Bucket
from backdrop.core.errors import ValidationError
from backdrop.core.records import Record
from backdrop.read.query import Query
from tests.support.test_helpers import d, d_tz


def mock_database(mock_repository):
    mock_database = Mock()
    mock_database.get_repository.return_value = mock_repository
    return mock_database


def mock_repository():
    mock_repository = Mock()
    mock_repository.find.return_value = []
    mock_repository.group.return_value = []
    return mock_repository


class TestBucket(unittest.TestCase):

    def setUp(self):
        self.mock_repository = mock_repository()
        self.mock_database = mock_database(self.mock_repository)
        self.bucket = bucket.Bucket(self.mock_database, 'test_bucket')

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
        self.bucket.query(Query.create(filter_by=[['name', 'Chico']]))
        self.mock_repository.find.assert_called_once()

    def test_group_by_query(self):
        self.mock_repository.group.return_value = [
            {"name": "Max", "_count": 3},
            {"name": "Gareth", "_count": 2}
        ]

        query = Query.create(group_by="name")
        query_result = self.bucket.query(query).data()

        self.mock_repository.group.assert_called_once_with(
            "name", query, None, None, [])

        assert_that(query_result,
                    has_item(has_entries({
                        'name': equal_to('Max'),
                        '_count': equal_to(3)})))
        assert_that(query_result,
                    has_item(has_entries({
                        'name': equal_to('Gareth'),
                        '_count': equal_to(2)})))

    def test_sorted_group_by_query(self):
        query = Query.create(group_by="name",
                             sort_by=["name", "ascending"])
        self.bucket.query(query)

        self.mock_repository.group.assert_called_once_with(
            "name", query, ["name", "ascending"], None, [])

    def test_sorted_group_by_query_with_limit(self):
        query = Query.create(group_by="name",
                             sort_by=["name", "ascending"], limit=100)
        self.bucket.query(query)

        self.mock_repository.group.assert_called_once_with(
            "name", query, ["name", "ascending"], 100, [])

    def test_group_by_query_with_collect(self):
        query = Query.create(group_by="name", sort_by=None, limit=None,
                             collect=["key"])
        self.bucket.query(query)

        self.mock_repository.group.assert_called_once_with(
            "name", query, None, None, ["key"])

    def test_query_with_start_at(self):
        query = Query.create(start_at=d(2013, 4, 1, 12, 0, 0))
        self.bucket.query(query)
        self.mock_repository.find.assert_called_with(
            query, sort=None, limit=None)

    def test_query_with_end_at(self):
        query = Query.create(end_at=d(2013, 4, 1, 12, 0, 0))
        self.bucket.query(query)

        self.mock_repository.find.assert_called_with(
            query, sort=None, limit=None)

    def test_query_with_start_at_and__end_at(self):
        query = Query.create(end_at=d(2013, 3, 1, 12, 0, 0),
                             start_at=d(2013, 2, 1, 12, 0, 0))
        self.bucket.query(query)

        self.mock_repository.find.assert_called_with(query, sort=None,
                                                     limit=None)

    def test_query_with_sort(self):
        query = Query.create(sort_by=["keyname", "descending"])
        self.bucket.query(query)

        self.mock_repository.find.assert_called_with(
            query, sort=["keyname", "descending"], limit=None
        )

    def test_query_with_limit(self):
        query = Query.create(limit=5)
        self.bucket.query(query)

        self.mock_repository.find.assert_called_with(query, sort=None, limit=5)

    def test_week_query(self):
        self.mock_repository.group.return_value = [
            {"_week_start_at": d(2013, 1, 7, 0, 0, 0), "_count": 3},
            {"_week_start_at": d(2013, 1, 14, 0, 0, 0), "_count": 1},
        ]

        query = Query.create(period='week')
        query_result = self.bucket.query(query).data()

        self.mock_repository.group.assert_called_once_with(
            "_week_start_at", query, sort=['_week_start_at', 'ascending'],
            limit=None)

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

    def test_month_query(self):
        self.mock_repository.group.return_value = [
            {"_month_start_at": d(2013, 4, 1), "_count": 1},
            {"_month_start_at": d(2013, 5, 1), "_count": 3}
        ]

        query = Query.create(period="month")
        query_result = self.bucket.query(query).data()
        self.mock_repository.group.assert_called_once_with(
            "_month_start_at", query, sort=['_month_start_at', 'ascending'],
            limit=None)

    def test_week_query_with_limit(self):
        self.mock_repository.group.return_value = []

        query = Query.create(period='week', limit=1)
        self.bucket.query(query)

        self.mock_repository.group.assert_called_once_with(
            "_week_start_at", query, sort=['_week_start_at', 'ascending'],
            limit=1)

    def test_month_query_with_limit(self):
        self.mock_repository.group.return_value = []

        query = Query.create(period='month', limit=1)
        self.bucket.query(query)

        self.mock_repository.group.assert_called_once_with(
            "_month_start_at", query, sort=['_month_start_at', 'ascending'],
            limit=1)

    def test_period_query_fails_when_weeks_do_not_start_on_monday(self):
        self.mock_repository.group.return_value = [
            {"_week_start_at": d(2013, 1, 7, 0, 0, 0), "_count": 3},
            {"_week_start_at": d(2013, 1, 8, 0, 0, 0), "_count": 1},
        ]

        self.assertRaises(
            ValueError,
            self.bucket.query,
            Query.create(period='week')
        )

    def test_period_query_fails_when_months_do_not_start_on_the_1st(self):
        self.mock_repository.group.return_value = [
            {"_month_start_at": d(2013, 1, 7, 0, 0, 0), "_count": 3},
            {"_month_start_at": d(2013, 2, 8, 0, 0, 0), "_count": 1},
        ]

        self.assertRaises(
            ValueError,
            self.bucket.query,
            Query.create(period='month')
        )

    def test_period_query_adds_missing_periods_in_correct_order(self):
        self.mock_repository.group.return_value = [
            {"_week_start_at": d(2013, 1, 14, 0, 0, 0), "_count": 32},
            {"_week_start_at": d(2013, 1, 21, 0, 0, 0), "_count": 45},
            {"_week_start_at": d(2013, 2, 4, 0, 0, 0), "_count": 17},
        ]

        result = self.bucket.query(Query.create(period='week',
                                                start_at=d_tz(2013, 1, 7, 0, 0,
                                                              0),
                                                end_at=d_tz(2013, 2, 18, 0, 0,
                                                            0)))

        assert_that(result.data(), contains(
            has_entries({"_start_at": d_tz(2013, 1, 7), "_count": 0}),
            has_entries({"_start_at": d_tz(2013, 1, 14), "_count": 32}),
            has_entries({"_start_at": d_tz(2013, 1, 21), "_count": 45}),
            has_entries({"_start_at": d_tz(2013, 1, 28), "_count": 0}),
            has_entries({"_start_at": d_tz(2013, 2, 4), "_count": 17}),
            has_entries({"_start_at": d_tz(2013, 2, 11), "_count": 0}),
        ))

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
        query_result = self.bucket.query(
            Query.create(period="week", group_by="some_group")).data()
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

    def test_month_and_group_query(self):
        self.mock_repository.multi_group.return_value = [
            {
                "some_group": "val1",
                "_count": 6,
                "_group_count": 2,
                "_subgroup": [
                    {
                        "_month_start_at": d(2013, 1, 1, 0, 0, 0),
                        "_count": 1
                    },
                    {
                        "_month_start_at": d(2013, 2, 1, 0, 0, 0),
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
                        "_month_start_at": d(2013, 3, 1, 0, 0, 0),
                        "_count": 2
                    },
                    {
                        "_month_start_at": d(2013, 4, 1, 0, 0, 0),
                        "_count": 6
                    },
                    {
                        "_month_start_at": d(2013, 7, 1, 0, 0, 0),
                        "_count": 6
                    }
                ]
            }
        ]

        query_result = self.bucket.query(Query.create(period="month",
                                                      group_by="some_group"))
        data = query_result.data()
        assert_that(data, has_item(has_entries({"values": has_length(2)})))
        assert_that(data, has_item(has_entries({"values": has_length(3)})))

    def test_month_and_group_query_with_start_and_end_at(self):
        self.mock_repository.multi_group.return_value = [
            {
                "some_group": "val1",
                "_count": 6,
                "_group_count": 2,
                "_subgroup": [
                    {
                        "_month_start_at": d(2013, 1, 1, 0, 0, 0),
                        "_count": 1
                    },
                    {
                        "_month_start_at": d(2013, 2, 1, 0, 0, 0),
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
                        "_month_start_at": d(2013, 3, 1, 0, 0, 0),
                        "_count": 2
                    },
                    {
                        "_month_start_at": d(2013, 4, 1, 0, 0, 0),
                        "_count": 6
                    },
                    {
                        "_month_start_at": d(2013, 7, 1, 0, 0, 0),
                        "_count": 6
                    }
                ]
            }
        ]

        query_result = self.bucket.query(Query.create(period="month",
                                                      group_by="some_group",
                                                      start_at=d(2013, 1, 1),
                                                      end_at=d(2013, 4, 2)))
        data = query_result.data()
        assert_that(data, has_item(has_entries({"values": has_length(4)})))
        assert_that(data, has_item(has_entries({"values": has_length(4)})))

        first_group = data[0]["values"]
        assert_that(first_group, has_item(has_entries({
            "_start_at": d_tz(2013, 3, 1)})))
        assert_that(first_group, has_item(has_entries({
            "_start_at": d_tz(2013, 4, 1)})))

        first_group = data[1]["values"]
        assert_that(first_group, has_item(has_entries({
            "_start_at": d_tz(2013, 1, 1)})))
        assert_that(first_group, has_item(has_entries({
            "_start_at": d_tz(2013, 2, 1)})))

    def test_period_group_query_adds_missing_periods_in_correct_order(self):
        self.mock_repository.multi_group.return_value = [
            {
                "some_group": "val1",
                "_count": 6,
                "_group_count": 2,
                "_subgroup": [
                    {
                        "_week_start_at": d(2013, 1, 14, 0, 0, 0),
                        "_count": 23
                    },
                    {
                        "_week_start_at": d(2013, 1, 21, 0, 0, 0),
                        "_count": 41
                    }
                ]
            },
            {
                "some_group": "val2",
                "_count": 8,
                "_group_count": 2,
                "_subgroup": [
                    {
                        "_week_start_at": d(2013, 1, 14, 0, 0, 0),
                        "_count": 31
                    },
                    {
                        "_week_start_at": d(2013, 1, 28, 0, 0, 0),
                        "_count": 12
                    }
                ]
            }
        ]

        query_result = self.bucket.query(
            Query.create(period="week", group_by="some_group",
                         start_at=d_tz(2013, 1, 7, 0, 0, 0),
                         end_at=d_tz(2013, 2, 4, 0, 0, 0))).data()

        assert_that(query_result, has_item(has_entries({
            "some_group": "val1",
            "values": contains(
                has_entries({"_start_at": d_tz(2013, 1, 7), "_count": 0}),
                has_entries({"_start_at": d_tz(2013, 1, 14), "_count": 23}),
                has_entries({"_start_at": d_tz(2013, 1, 21), "_count": 41}),
                has_entries({"_start_at": d_tz(2013, 1, 28), "_count": 0}),
            ),
        })))

        assert_that(query_result, has_item(has_entries({
            "some_group": "val2",
            "values": contains(
                has_entries({"_start_at": d_tz(2013, 1, 7), "_count": 0}),
                has_entries({"_start_at": d_tz(2013, 1, 14), "_count": 31}),
                has_entries({"_start_at": d_tz(2013, 1, 21), "_count": 0}),
                has_entries({"_start_at": d_tz(2013, 1, 28), "_count": 12}),
            ),
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

        query = Query.create(period="week", group_by="some_group",
                             sort_by=["_count", "descending"])
        self.bucket.query(query)

        self.mock_repository.multi_group.assert_called_with(
            "some_group",
            "_week_start_at",
            query,
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

        query = Query.create(period="week", group_by="some_group",
                             sort_by=["_count", "descending"], limit=1,
                             collect=[])
        self.bucket.query(query)

        self.mock_repository.multi_group.assert_called_with(
            "some_group",
            "_week_start_at",
            query,
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
            self.bucket.query(Query.create(period='week', group_by='d')).data()
            assert_that(False)
        except ValueError as e:
            assert_that(str(e), is_(
                "Weeks MUST start on Monday but got date: 2013-04-09 00:00:00"
            ))


class TestBucketAutoIdGeneration(unittest.TestCase):
    def setUp(self):
        self.mock_repository = mock_repository()
        self.mock_database = mock_database(self.mock_repository)

    def test_auto_id_generation(self):
        objects = [{
            "postcode": "WC2B 6SE",
            "number": "125",
            "name": "Aviation House"
        }]

        auto_id = ("postcode", "number")
        bucket = Bucket(self.mock_database, "bucket", generate_id_from=auto_id)

        bucket.parse_and_store(objects)

        self.mock_repository.save.assert_called_once_with({
            "_id": b64encode("WC2B 6SE.125"),
            "postcode": "WC2B 6SE",
            "number": "125",
            "name": "Aviation House"
        })

    def test_no_id_generated_if_auto_id_is_none(self):
        object = {
            "postcode": "WC2B 6SE",
            "number": "125",
            "name": "Aviation House"
        }

        bucket = Bucket(self.mock_database, "bucket", generate_id_from=None)

        bucket.parse_and_store([object])

        self.mock_repository.save.assert_called_once_with(object)

    @raises(ValidationError)
    def test_validation_error_if_auto_id_property_is_missing(self):
        objects = [{
            "postcode": "WC2B 6SE",
            "name": "Aviation House"
        }]

        auto_id = ("postcode", "number")
        bucket = Bucket(self.mock_database, "bucket", generate_id_from=auto_id)

        bucket.parse_and_store(objects)

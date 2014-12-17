import unittest

from hamcrest import assert_that, is_

from backdrop.transformers.tasks.user_satisfaction import compute


data = [
    {
        "_count": 7.0,
        "_start_at": "2014-11-10T00:00:00+00:00",
        "_end_at": "2014-11-17T00:00:00+00:00",
        "rating_1:sum": 1.0,
        "rating_2:sum": 1.0,
        "rating_3:sum": 1.0,
        "rating_4:sum": 1.0,
        "rating_5:sum": 1.0,
        "total:sum": 5.0
    },
    {
        "_count": 7.0,
        "_start_at": "2014-11-17T00:00:00+00:00",
        "_end_at": "2014-11-24T00:00:00+00:00",
        "rating_1:sum": 1.0,
        "rating_2:sum": 1.0,
        "rating_3:sum": 1.0,
        "rating_4:sum": 1.0,
        "rating_5:sum": 6.0,
        "total:sum": 10.0
    },
    {
        "_count": 7.0,
        "_start_at": "2014-11-24T00:00:00+00:00",
        "_end_at": "2014-12-01T00:00:00+00:00",
        "rating_1:sum": 6.0,
        "rating_2:sum": 1.0,
        "rating_3:sum": 1.0,
        "rating_4:sum": 1.0,
        "rating_5:sum": 1.0,
        "total:sum": 10.0
    },
    {
        "_count": 0.0,
        "_start_at": "2014-12-01T00:00:00+00:00",
        "_end_at": "2014-12-08T00:00:00+00:00",
        "rating_1:sum": None,
        "rating_2:sum": None,
        "rating_3:sum": None,
        "rating_4:sum": None,
        "rating_5:sum": None,
        "total:sum": None
    },
    {
        "_count": 7.0,
        "_start_at": "2014-12-01T00:00:00+00:00",
        "_end_at": "2014-12-08T00:00:00+00:00",
        "rating_1:sum": 0.0,
        "rating_2:sum": 0.0,
        "rating_3:sum": 0.0,
        "rating_4:sum": 0.0,
        "rating_5:sum": 0.0,
        "total:sum": 0.0
    }
]


class UserSatisfactionTestCase(unittest.TestCase):
    def test_compute_user_satisfaction(self):
        transformed_data = compute(data, {})

        assert_that(len(transformed_data), is_(5))
        assert_that(
            transformed_data[0]['_id'],
            is_('MjAxNC0xMS0xMFQwMDowMDowMCswMDowMF8yMDE0LTExLTE3VDAwOjAwOjAwKzAwOjAw'))
        assert_that(
            transformed_data[0]['_timestamp'],
            is_('2014-11-10T00:00:00+00:00'))
        assert_that(
            transformed_data[0]['_start_at'],
            is_('2014-11-10T00:00:00+00:00'))
        assert_that(
            transformed_data[0]['_end_at'],
            is_('2014-11-17T00:00:00+00:00'))
        assert_that(transformed_data[0]['rating'], is_(0.5))
        assert_that(transformed_data[1]['rating'], is_(0.75))
        assert_that(transformed_data[2]['rating'], is_(0.25))
        assert_that(transformed_data[3]['rating'], is_(None))
        assert_that(transformed_data[4]['rating'], is_(None))

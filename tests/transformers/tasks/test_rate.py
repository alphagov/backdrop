import unittest

from hamcrest import assert_that, is_

from backdrop.transformers.tasks.rate import compute

data = [
    {
        "_end_at": '2013-12-02T00:00:00+00:00',
        "_start_at": '2013-11-25T00:00:00+00:00',
        "eventCategory": 'start',
        "uniqueEvents:sum": 15.0
    },
    {
        "_end_at": '2013-12-09T00:00:00+00:00',
        "_start_at": '2013-12-02T00:00:00+00:00',
        "eventCategory": 'start',
        "uniqueEvents:sum": 25.0
    },
    {
        "_end_at": '2013-12-02T00:00:00+00:00',
        "_start_at": '2013-11-25T00:00:00+00:00',
        "eventCategory": 'confirm',
        "uniqueEvents:sum": 8.0
    },
    {
        "_end_at": '2013-12-09T00:00:00+00:00',
        "_start_at": '2013-12-02T00:00:00+00:00',
        "eventCategory": 'confirm',
        "uniqueEvents:sum": 12.0
    },
    {
        "_end_at": '2013-12-02T00:00:00+00:00',
        "_start_at": '2013-11-25T00:00:00+00:00',
        "eventCategory": 'done',
        "uniqueEvents:sum": 10.0
    },
    {
        "_end_at": '2013-12-09T00:00:00+00:00',
        "_start_at": '2013-12-02T00:00:00+00:00',
        "eventCategory": 'done',
        "uniqueEvents:sum": None
    }
]


class ComputeTestCase(unittest.TestCase):
    def test_compute(self):
        transformed_data = compute(data, {
            "denominatorMatcher": 'start',
            "numeratorMatcher": 'done',
            "matchingAttribute": 'eventCategory',
            "valueAttribute": 'uniqueEvents:sum',
        })

        assert_that(len(transformed_data), is_(2))
        assert_that(
            transformed_data[0]['_id'],
            is_('MjAxMy0xMS0yNVQwMDowMDowMCswMDowMF8yMDEzLTEyLTAyVDAwOjAwOjAwKzAwOjAw'))
        assert_that(
            transformed_data[0]['_timestamp'],
            is_('2013-11-25T00:00:00+00:00'))
        assert_that(
            transformed_data[0]['_start_at'],
            is_('2013-11-25T00:00:00+00:00'))
        assert_that(
            transformed_data[0]['_end_at'],
            is_('2013-12-02T00:00:00+00:00'))
        assert_that(transformed_data[0]['rate'], is_(2.0 / 3.0))
        assert_that(transformed_data[1]['rate'], is_(None))

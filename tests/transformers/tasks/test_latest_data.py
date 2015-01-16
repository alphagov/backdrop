import unittest

from hamcrest import assert_that, is_

from backdrop.transformers.tasks.latest_data import compute

data = [
    {
      "_day_start_at": "2013-10-07T00:00:00+00:00",
      "_end_at": "2013-10-14T00:00:00+00:00",
      "_hour_start_at": "2013-10-07T00:00:00+00:00",
      "_id": "MjAxMy0xMC0wN1QwMDowMDowMCswMDowMF8yMDEzLTEwLTE0VDAwOjAwOjAwKzAwOjAw",
      "_month_start_at": "2013-10-01T00:00:00+00:00",
      "_quarter_start_at": "2013-10-01T00:00:00+00:00",
      "_start_at": "2013-10-07T00:00:00+00:00",
      "_timestamp": "2013-10-07T00:00:00+00:00",
      "_updated_at": "2015-01-14T12:51:45.621000+00:00",
      "_week_start_at": "2013-10-07T00:00:00+00:00",
      "_year_start_at": "2013-01-01T00:00:00+00:00",
      "rate": 0.26958105646630237
    },
    {
      "_day_start_at": "2013-10-14T00:00:00+00:00",
      "_end_at": "2013-10-21T00:00:00+00:00",
      "_hour_start_at": "2013-10-14T00:00:00+00:00",
      "_id": "MjAxMy0xMC0xNFQwMDowMDowMCswMDowMF8yMDEzLTEwLTIxVDAwOjAwOjAwKzAwOjAw",
      "_month_start_at": "2013-10-01T00:00:00+00:00",
      "_quarter_start_at": "2013-10-01T00:00:00+00:00",
      "_start_at": "2013-10-14T00:00:00+00:00",
      "_timestamp": "2013-10-14T00:00:00+00:00",
      "_updated_at": "2015-01-14T12:51:45.624000+00:00",
      "_week_start_at": "2013-10-14T00:00:00+00:00",
      "_year_start_at": "2013-01-01T00:00:00+00:00",
      "rate": 0.29334396173774413
    },
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

    def test_regex_matching_supports_carets(self):
        # The numeratorMatcher should match just "digital"
        # The denominatorMatcher should match both "digital" and "non-digital"
        transformed_data = compute(data, {
            "denominatorMatcher": 'digital$',
            "numeratorMatcher": '^digital$',
            "matchingAttribute": 'channel',
            "valueAttribute": 'uniqueEvents:sum',
        })

        assert_that(transformed_data[0]['rate'], is_(8.0 / (8.0 + 15.0)))
        assert_that(transformed_data[1]['rate'], is_(12.0 / (12.0 + 25.0)))

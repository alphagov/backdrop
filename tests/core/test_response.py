from unittest import TestCase
from hamcrest import assert_that, is_, has_length, has_key
from nose.tools import assert_raises, nottest

import pytz
import datetime

from backdrop.core.response import PeriodFlatData
from backdrop.core.timeseries import timeseries_the_return_of_the_keys, MONTH

from itertools import groupby


class TestPeriodFlatData(TestCase):

    def test_include_all_key_permutations(self):
        """
        Test that the response includes all permutations of group_by parameters.
        """

        data = [
            {
                '_end_at': datetime.datetime(2013, 2, 1, 0, 0, tzinfo=pytz.UTC),
                '_count': 17.0,
                'paymentStatus': 'Success',
                'paymentThing': 'blue',
                'no': 'yes',
                '_start_at': datetime.datetime(2013, 1, 1, 0, 0, tzinfo=pytz.UTC)
            },
            {
                '_end_at': datetime.datetime(2013, 2, 1, 0, 0, tzinfo=pytz.UTC),
                '_count': 18.0,
                'paymentStatus': 'Unknown',
                'paymentThing': 'elephant',
                'no': 'maybe',
                '_start_at': datetime.datetime(2013, 1, 1, 0, 0, tzinfo=pytz.UTC)
            },
            {
                '_end_at': datetime.datetime(2013, 2, 1, 0, 0, tzinfo=pytz.UTC),
                '_count': 30.0,
                'paymentStatus': '',
                'paymentThing': 'kant',
                'no': 'maybe',
                '_start_at': datetime.datetime(2013, 1, 1, 0, 0, tzinfo=pytz.UTC)
            }
        ]

        series = timeseries_the_return_of_the_keys(start=datetime.datetime(2013, 1, 1, 0, 0, tzinfo=pytz.UTC),
                                          end=datetime.datetime(2013, 2, 1, 0, 0, tzinfo=pytz.UTC),
                                          period=MONTH,
                                          data=data,
                                          default={"_count": 0})

        assert_that(series, has_length(18))


    def test_multiple_group_by_months(self):
        """
        Test that the response correctly returns multiple time periods with group by keys.
        """

        first_month_start = datetime.datetime(2013, 1, 1, 0, 0, tzinfo=pytz.UTC)
        second_month_start = datetime.datetime(2013, 2, 1, 0, 0, tzinfo=pytz.UTC)

        data = [
            {
                '_end_at': datetime.datetime(2013, 2, 1, 0, 0, tzinfo=pytz.UTC),
                '_count': 17.0,
                'paymentStatus': 'Success',
                'paymentThing': 'blue',
                'no': 'yes',
                '_start_at': first_month_start
            },
            {
                '_end_at': datetime.datetime(2013, 3, 1, 0, 0, tzinfo=pytz.UTC),
                '_count': 18.0,
                'paymentStatus': 'Unknown',
                'paymentThing': 'elephant',
                'no': 'maybe',
                '_start_at': second_month_start
            },
        ]

        series = timeseries_the_return_of_the_keys(start=datetime.datetime(2013, 1, 1, 0, 0, tzinfo=pytz.UTC),
                                                   end=datetime.datetime(2013, 3, 1, 0, 0, tzinfo=pytz.UTC),
                                                   period=MONTH,
                                                   data=data,
                                                   default={"_count": 0})

        assert_that(series, has_length(16))

        # Assert the correct date spans have been returned
        first_month = [point for point in series if point['_start_at'] == first_month_start]
        assert_that(first_month, has_length(8))
        second_month = [point for point in series if point['_start_at'] == second_month_start]
        assert_that(second_month, has_length(8))

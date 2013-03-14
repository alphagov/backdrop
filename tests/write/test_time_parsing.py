from datetime import datetime
import unittest

from hamcrest import *
import pytz

from backdrop.write.api import time_string_to_utc_datetime


class DateStringToUTCDateTimeTestCase(unittest.TestCase):
    def test_that_date_strings_get_converted_to_datetimes(self):
        some_datetime = time_string_to_utc_datetime(
            '2014-01-02T03:04:05+00:00')

        assert_that(isinstance(some_datetime, datetime), is_(True))
        assert_that(some_datetime,
                    is_(datetime(2014, 1, 2, 3, 4, 5, tzinfo=pytz.utc)))

    def test_that_date_strings_get_converted_to_utc(self):
        some_datetime = time_string_to_utc_datetime(
            '2014-01-02T06:04:05+03:30')

        assert_that(isinstance(some_datetime, datetime), is_(True))
        assert_that(some_datetime,
                    is_(datetime(2014, 1, 2, 2, 34, 5, tzinfo=pytz.utc)))

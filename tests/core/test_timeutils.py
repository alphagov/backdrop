import unittest
from hamcrest import assert_that, equal_to
import pytz
from backdrop.core.timeutils import parse_time_as_utc
from tests.support.test_helpers import d_tz, d


class ParseTimeAsUTCTestCase(unittest.TestCase):
    def test_valid_time_string_is_parsed(self):
        assert_that(parse_time_as_utc("2012-12-12T12:12:12+00:00"),
                    equal_to(d_tz(2012, 12, 12, 12, 12, 12)))

    def test_time_string_is_converted_to_utc(self):
        assert_that(parse_time_as_utc("2012-12-12T12:12:12+01:00"),
                    equal_to(d_tz(2012, 12, 12, 11, 12, 12)))

    def test_invalid_time_string_raises_value_error(self):
        self.assertRaises(ValueError, parse_time_as_utc, "not a date")

    def test_datetime_is_converted_to_utc(self):
        us_eastern_time = d_tz(2012, 12, 12, 12,
                               tzinfo=pytz.timezone("US/Eastern"))
        assert_that(parse_time_as_utc(us_eastern_time),
                    equal_to(d_tz(2012, 12, 12, 17)))

    def test_datetime_with_no_timezone_is_given_utc(self):
        assert_that(parse_time_as_utc(d(2012, 12, 12, 12)),
                    equal_to(d_tz(2012, 12, 12, 12)))

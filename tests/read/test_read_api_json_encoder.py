import unittest
import pytz

from hamcrest import *
from datetime import datetime
from backdrop.read.api import JsonEncoder


class TestReadAPIJSONEcoder(unittest.TestCase):

    def test_with_utc_date(self):
        obj = {'date': datetime(2014, 4, 29, 1, 0, 0, 0, pytz.utc)}
        assert_that(
            JsonEncoder().encode(obj),
            is_('{"date": "2014-04-29T01:00:00+00:00"}'))

    def test_with_est_date(self):
        est = pytz.timezone('US/Eastern')
        obj = {'date': datetime(2014, 4, 29, 1, 0, 0, 0, est)}
        assert_that(
            JsonEncoder().encode(obj),
            is_('{"date": "2014-04-29T06:00:00+00:00"}'))

    def test_with_no_tz_date(self):
        obj = {'date': datetime(2014, 4, 29, 1, 0)}
        assert_that(
            JsonEncoder().encode(obj),
            is_('{"date": "2014-04-29T01:00:00+00:00"}'))

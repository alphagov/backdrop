import datetime
import unittest

from hamcrest import assert_that, is_

from backdrop.write.api import bounding_dates


class BoundingDatesTestCase(unittest.TestCase):

    def test_bounding_dates(self):
        data = [
            {'_timestamp': datetime.datetime(2014, 9, 3)},
            {'_timestamp': datetime.datetime(2014, 9, 9)},
            {'_timestamp': datetime.datetime(2014, 9, 7)},
            {'_timestamp': datetime.datetime(2014, 9, 1)},
        ]

        earliest, latest = bounding_dates(data)

        assert_that(earliest.day, is_(1))
        assert_that(latest.day, is_(9))

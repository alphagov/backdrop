import unittest
import datetime

from licensing.data import location

class TestDateUtils(unittest.TestCase):
    def test_first_day_of_month(self):
        date = location.first_day_of_month(datetime.date(2012, 12, 12))

        self.assertEquals(date, datetime.date(2012, 12, 1))

    def test_get_last_whole_month(self):
        start, end = location.get_last_whole_month(datetime.date(2012, 12, 12))

        self.assertEquals(start, datetime.date(2012, 11, 1))
        self.assertEquals(end, datetime.date(2012, 11, 30))
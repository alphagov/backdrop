import unittest
from hamcrest import *
from backdrop.read.response import create_period_group_month
from tests.support.test_helpers import d, d_tz


class TestResponseMethods(unittest.TestCase):
    def test_building_month_groups(self):
        doc = {"_month_start_at": d(2013, 4, 1), "_count": 0}
        expanded_doc = create_period_group_month(doc)
        assert_that(expanded_doc, has_entry("_start_at", d_tz(2013, 4, 1)))
        assert_that(expanded_doc, has_entry("_end_at", d_tz(2013, 5, 1)))

    def test_building_month_groups_on_year_boundaries(self):
        doc = {"_month_start_at": d(2013, 12, 1), "_count": 0}
        expanded_doc = create_period_group_month(doc)
        assert_that(expanded_doc, has_entry("_start_at", d_tz(2013, 12, 1)))
        assert_that(expanded_doc, has_entry("_end_at", d_tz(2014, 1, 1)))

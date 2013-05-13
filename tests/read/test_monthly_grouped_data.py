import unittest
from hamcrest import *
from backdrop.core.timeseries import timeseries, MONTH
from backdrop.read.response import create_period_group_month, MonthlyGroupedData
from tests.support.test_helpers import d


class TestMonthlyGroupedData(unittest.TestCase):
    def test_adding_mongo_document(self):
        stub_document = {"_subgroup": []}
        data = MonthlyGroupedData([stub_document])
        assert_that(data.data(), has_length(1))

    def test_month_start_at_gets_expanded_into_start_and_end_fields(self):
        stub_document = {
            "_subgroup": [{
                "_month_start_at": d(2013, 4, 1),
                "_count": 1
            }]}
        data = MonthlyGroupedData([stub_document])
        values = data.data()[0]['values']
        assert_that(values, has_length(1))

    def test_filling_missing_months(self):
        stub_document = {
            "_subgroup": [
                {
                    "_month_start_at": d(2013, 4, 1),
                    "_count": 1
                },
                {
                    "_month_start_at": d(2013, 6, 1),
                    "_count": 1
                }]
        }
        data = MonthlyGroupedData([stub_document])
        data.fill_missing_months(d(2013, 4, 1), d(2013, 6, 2))
        values = data.data()[0]["values"]
        assert_that(values, has_length(3))

    def test_adding_unrecognized_data_throws_an_error(self):
        stub_document = {"foo": "bar"}
        try:
            MonthlyGroupedData([stub_document])
            assert_that(False, "Expected an exception")
        except ValueError as e:
            assert_that(str(e), is_("Expected document to have "
                                    "key '_subgroup'"))

    def test_adding_subgroups_of_unrecognized_format_throws_an_error(self):
        stub_document = {"_subgroup": {"foo": "bar"}}
        try:
            MonthlyGroupedData([stub_document])
            assert_that(False, "Expected an exception")
        except ValueError as e:
            assert_that(str(e), is_("Expected subgroup to have "
                                    "keys '_count' and '_month_start_at'"))

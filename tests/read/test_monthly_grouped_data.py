import unittest
from nose.tools import *
from hamcrest import *
from backdrop.core.timeseries import MONTH
from backdrop.core.response import PeriodGroupedData
from tests.support.test_helpers import d


class TestMonthlyGroupedData(unittest.TestCase):
    def test_adding_mongo_document(self):
        stub_document = {"_subgroup": []}
        data = PeriodGroupedData([stub_document], MONTH)
        assert_that(data.data(), has_length(1))

    def test_month_start_at_gets_expanded_into_start_and_end_fields(self):
        stub_document = {
            "_subgroup": [{
                "_month_start_at": d(2013, 4, 1),
                "_count": 1
            }]}
        data = PeriodGroupedData([stub_document], MONTH)
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
        data = PeriodGroupedData([stub_document], MONTH)
        data.fill_missing_periods(d(2013, 4, 1), d(2013, 6, 2))
        values = data.data()[0]["values"]
        assert_that(values, has_length(3))

    def test_adding_unrecognized_data_throws_an_error(self):
        stub_document = {"foo": "bar"}
        assert_raises(ValueError, PeriodGroupedData, [stub_document], MONTH)

    def test_adding_subgroups_of_unrecognized_format_throws_an_error(self):
        stub_document = {"_subgroup": {"foo": "bar"}}
        assert_raises(ValueError, PeriodGroupedData, [stub_document], MONTH)

    def test_that_other_fields_get_added_to_response(self):
        stub_document = {
            "_subgroup": [
                {
                    "_month_start_at": d(2013, 5, 1),
                    "_count": 1
                }
            ],
            "other_stuff": "something"
        }

        data = PeriodGroupedData([stub_document], MONTH)

        assert_that(data.data()[0], has_entry("other_stuff", "something"))

    def test_that_collected_values_are_preserved(self):
        stub_document = {
            "_subgroup": [
                {
                    "_month_start_at": d(2013, 5, 1),
                    "_count": 1,
                    "foo:sum": 123
                }
            ]
        }

        data = PeriodGroupedData([stub_document], MONTH)

        assert_that(data.data()[0]["values"][0],
                    has_entry("foo:sum", 123))

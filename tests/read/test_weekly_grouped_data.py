import unittest
from hamcrest import *
from backdrop.read.response import WeeklyGroupedData
from tests.support.test_helpers import d, d_tz


class TestWeeklyGroupedData(unittest.TestCase):
    def test_adding_documents(self):
        stub_document = {"_subgroup": []}
        data = WeeklyGroupedData()
        data.add(stub_document)
        assert_that(data.data(), has_length(1))

    def test_returned_data_should_be_immutable(self):
        stub_document = {"_subgroup": []}
        data = WeeklyGroupedData()
        data.add(stub_document)
        another_data = data.data()
        try:
            another_data.append({"even_more_nonsense": True})
            assert_that(False, "expected an exception")
        except AttributeError as e:
            assert_that(str(e), "'tuple' object has no attribute append")

    def test_adding_multiple_mongo_documents(self):
        stub_document_1 = {
            "_subgroup": [ {"_week_start_at": d(2013, 4, 1), "_count": 5} ]
        }
        stub_document_2 = {
            "_subgroup": [ {"_week_start_at": d(2013, 4, 1), "_count": 5} ]
        }
        data = WeeklyGroupedData()
        data.add(stub_document_1)
        data.add(stub_document_2)
        assert_that(data.data(), has_length(2))

    def test_week_start_at_gets_expanded_in_subgroups_when_added(self):
        stub_document = {
            "_subgroup": [
                {
                    "_week_start_at": d(2013, 4, 1),
                    "_count": 5
                }
            ]
        }
        data = WeeklyGroupedData()
        data.add(stub_document)
        values = data.data()[0]['values']
        assert_that(values, has_item(has_entry("_start_at", d_tz(2013, 4, 1))))
        assert_that(values, has_item(has_entry("_end_at", d_tz(2013, 4, 8))))
        assert_that(values, has_item(has_entry("_count", 5)))

    def test_adding_unrecognized_data_throws_an_error(self):
        stub_document = {"foo": "bar"}
        data = WeeklyGroupedData()
        try:
            data.add(stub_document)
            assert_that(False, "Expected an exception")
        except ValueError as e:
            assert_that(str(e), is_("Expected document to have "
                                    "key '_subgroup'"))

    def test_adding_subgroups_of_unrecognized_format_throws_an_error(self):
        stub_document = {"_subgroup": { "foo": "bar" }}
        data = WeeklyGroupedData()
        try:
            data.add(stub_document)
            assert_that(False, "Expected an exception")
        except ValueError as e:
            assert_that(str(e), is_("Expected subgroup to have "
                                    "keys '_count' and '_week_start_at'"))
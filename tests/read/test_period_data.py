import unittest
from hamcrest import *
from backdrop.read.response import PeriodData
from tests.support.test_helpers import d, d_tz


class TestPeriodData(unittest.TestCase):
    def test_adding_mongo_document_to_collection_expands_week_start_at(self):
        stub_doc = {
            "_week_start_at": d(2013, 5, 6),
            "_count": 42
        }

        period_data = PeriodData([stub_doc])

        assert_that(len(period_data.data()), is_(1))
        assert_that(period_data.data()[0], has_entry("_count", 42))
        assert_that(period_data.data()[0], has_entry("_start_at",
                                                     d_tz(2013, 5, 6)))
        assert_that(period_data.data()[0], has_entry("_end_at",
                                                     d_tz(2013, 5, 13)))

    def test_period_datum_week_start_at_should_be_monday(self):
        stub_doc = {
            "_week_start_at": d(2013, 5, 4),
            "_count": 0
        }

        try:
            period_data = PeriodData([stub_doc])
            assert_that(False, "expected exception")
        except ValueError as e:
            assert_that(str(e), is_("Weeks MUST start on Monday but got date:"
                                    " " + str(d(2013, 5, 4))))

    def test_adding_more_mongo_documents_to_collection(self):
        stub_doc = {
            "_week_start_at": d(2013, 5, 6),
            "_count": 42
        }
        another_stub_doc = {
            "_week_start_at": d(2013, 5, 13),
            "_count": 66
        }

        period_data = PeriodData([stub_doc, another_stub_doc])

        assert_that(len(period_data.data()), is_(2))

        assert_that(period_data.data()[0], has_entry("_start_at",
                                                     d_tz(2013, 5, 6)))
        assert_that(period_data.data()[0], has_entry("_end_at",
                                                     d_tz(2013, 5, 13)))

        assert_that(period_data.data()[1], has_entry("_start_at",
                                                     d_tz(2013, 5, 13)))
        assert_that(period_data.data()[1], has_entry("_end_at",
                                                     d_tz(2013, 5, 20)))

    def test_returned_data_should_be_immutable(self):
        stub_doc = {
            "_week_start_at": d(2013, 5, 6),
            "_count": 42
        }
        period_data = PeriodData([stub_doc])
        the_data = period_data.data()
        try:
            the_data.append({"nonsense": True})
            assert_that(False, "expected an exception")
        except AttributeError as e:
            assert_that(str(e), "'tuple' object has no attribute append")

    def test_filling_data_for_missing_periods(self):
        stub_doc_1 = {
            "_week_start_at": d(2013, 4, 1),
            "_count": 5
        }
        stub_doc_2 = {
            "_week_start_at": d(2013, 4, 15),
            "_count": 5
        }
        period_data = PeriodData([stub_doc_1, stub_doc_2])

        period_data.fill_missing_weeks(d(2013, 4, 1), d(2013, 4, 16))

        assert_that(period_data.data(), has_length(3))

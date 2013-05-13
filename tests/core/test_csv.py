from StringIO import StringIO
import unittest
from hamcrest import assert_that, only_contains, is_
from backdrop.core.parse_csv import parse_csv, MoreValuesThanColumnsException, MissingValuesForSomeColumnsException


class ParseCsvTestCase(unittest.TestCase):
    def test_parse_csv(self):
        csv_stream = StringIO("a,b\nx,y\nq,w")

        data = list(parse_csv(csv_stream))

        assert_that(data,
                    only_contains({"a": "x", "b": "y"}, {"a": "q", "b": "w"}))

    def test_parse_csv_when_values_for_columns_missing(self):
        csv_stream = StringIO("a,b\nx,y\nq")

        try:
            list(parse_csv(csv_stream))
            assert_that(False)
        except MissingValuesForSomeColumnsException as e:
            pass

    def test_parse_csv_when_more_values_than_columns(self):
        csv_stream = StringIO("a,b\nx,y,s,d\nq,w")

        try:
            list(parse_csv(csv_stream))
            assert_that(False)
        except MoreValuesThanColumnsException as e:
            pass

    def test_parse_empty_csv(self):
        csv_stream = StringIO("")

        data = list(parse_csv(csv_stream))

        assert_that(data, is_([]))

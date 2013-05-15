from StringIO import StringIO
import unittest
from hamcrest import assert_that, only_contains, is_

from backdrop.core.parse_csv import parse_csv
from backdrop.core.errors import ParseError


class ParseCsvTestCase(unittest.TestCase):
    def test_parse_csv(self):
        csv_stream = StringIO("a,b\nx,y\nq,w")

        data = parse_csv(csv_stream)

        assert_that(data,
                    only_contains({"a": "x", "b": "y"}, {"a": "q", "b": "w"}))

    def test_parse_empty_csv(self):
        csv_stream = StringIO("")

        data = parse_csv(csv_stream)

        assert_that(data, is_([]))

    def test_error_when_values_for_columns_are_missing(self):
        incoming_data = StringIO("a,b\nx,y\nq")

        self.assertRaises(ParseError, parse_csv, incoming_data)

    def test_error_when_there_are_more_values_than_columns(self):
        incoming_data = StringIO("a,b\nx,y,s,d\nq,w")

        self.assertRaises(ParseError, parse_csv, incoming_data)

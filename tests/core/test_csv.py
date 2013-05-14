from StringIO import StringIO
import unittest
from hamcrest import assert_that, only_contains, is_
from backdrop.core.parse_csv import parse_csv


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

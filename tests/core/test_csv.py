# -*- coding: utf-8 -*-

from cStringIO import StringIO
import unittest
from hamcrest import assert_that, only_contains, is_

from backdrop.core.parse_csv import parse_csv, lines
from backdrop.core.errors import ParseError


class ParseCsvTestCase(unittest.TestCase):
    def test_parse_csv(self):
        csv_stream = _string_io("a,b\nx,y\nq,w")

        data = parse_csv(csv_stream)

        assert_that(data,
                    only_contains({"a": "x", "b": "y"}, {"a": "q", "b": "w"}))

    def test_parse_empty_csv(self):
        csv_stream = _string_io("")

        data = parse_csv(csv_stream)

        assert_that(data, is_([]))

    def test_parse_utf8_data(self):
        csv = u"a,b\nà,ù"
        csv_stream = _string_io(csv, "utf-8")

        data = parse_csv(csv_stream)

        assert_that(data, only_contains(
            {"a": u"à", "b": u"ù"}
        ))

    def test_error_when_values_for_columns_are_missing(self):
        incoming_data = _string_io("a,b\nx,y\nq")

        self.assertRaises(ParseError, parse_csv, incoming_data)

    def test_error_when_there_are_more_values_than_columns(self):
        incoming_data = _string_io("a,b\nx,y,s,d\nq,w")

        self.assertRaises(ParseError, parse_csv, incoming_data)

    def test_error_when_input_is_not_utf8(self):
        csv = u"a,b\nà,ù"

        csv_stream = _string_io(csv, "iso-8859-1")

        self.assertRaises(ParseError, parse_csv, csv_stream)

    def test_ignore_when_empty_row(self):
        csv = u"a,b\n,\nc,d"
        csv_stream = _string_io(csv, "utf-8")

        data = parse_csv(csv_stream)

        assert_that(data, only_contains(
            {"a": u"c", "b": u"d"}
        ))

    def test_accept_when_some_values_empty(self):
        csv = u"a,b\n,\nc,d\nc,"
        csv_stream = _string_io(csv, "utf-8")

        data = parse_csv(csv_stream)

        assert_that(data, only_contains(
            {"a": u"c", "b": u"d"},
            {"a": u"c", "b": u""}
        ))

    def test_ignore_comments(self):
        csv = u"# top comment\na,b\n# any random comment\nc,d"
        csv_stream = _string_io(csv, "utf-8")

        data = parse_csv(csv_stream)

        assert_that(data, only_contains(
            {"a": u"c", "b": u"d"}
        ))

    def test_ignore_values_in_comments_column(self):
        csv = u"a,comment,b\nc,d,e"
        csv_stream = _string_io(csv, "utf-8")

        data = parse_csv(csv_stream)

        assert_that(data, only_contains(
            {"a": u"c", "b": u"e"}
        ))

    def test_accept_csv_with_CR_as_line_separator(self):
        csv = u"prop1,prop2\rvalue 1,value 2"
        csv_stream = _string_io(csv, "utf-8")

        data = parse_csv(csv_stream)

        assert_that(data, only_contains(
            {"prop1": "value 1", "prop2": "value 2"}
        ))

    def test_accept_csv_with_CRLF_as_line_separator(self):
        csv = u"prop1,prop2\r\nvalue 1,value 2"
        csv_stream = _string_io(csv, "utf-8")

        data = parse_csv(csv_stream)

        assert_that(data, only_contains(
            {"prop1": "value 1", "prop2": "value 2"}
        ))

    def test_preserve_newlines_in_quoted_values(self):
        csv = u"prop1,prop2\nvalue,\"value\nwith newline\""

        csv_stream = _string_io(csv, "utf-8")

        data = parse_csv(csv_stream)

        assert_that(data, only_contains(
            {"prop1": "value", "prop2": "value\nwith newline"}
        ))


class LinesGeneratorTest(unittest.TestCase):
    def test_handles_CR_LF_and_CRLF(self):
        text = "1\n2\r3\r\n4"

        lines_list = list(lines(_string_io(text)))

        assert_that(lines_list, is_(["1\n", "2\r", "3\r\n", "4"]))

    def test_handles_emptylines(self):
        text = "q\n\rw\r\r\ne"

        lines_list = list(lines(_string_io(text)))

        assert_that(lines_list, is_(["q\n", "\r", "w\r", "\r\n", "e"]))

    def test_ignores_trailing_empty_line(self):
        text = "asd\n"

        lines_list = list(lines(_string_io(text)))

        assert_that(lines_list, is_(["asd\n"]))


def _string_io(content, encoding=None):
    if encoding is not None:
        content = content.encode(encoding)
    return StringIO(content)

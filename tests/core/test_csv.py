from StringIO import StringIO
from hamcrest import assert_that, only_contains, is_
from backdrop.core.parse_csv import parse_csv


def test_parse_csv():
    csv_stream = StringIO("a,b\nx,y\nq,w")

    data = list(parse_csv(csv_stream))

    assert_that(data,
                only_contains({"a": "x", "b": "y"}, {"a": "q", "b": "w"}))


def test_parse_empty_csv():
    csv_stream = StringIO("")

    data = list(parse_csv(csv_stream))

    assert_that(data, is_([]))

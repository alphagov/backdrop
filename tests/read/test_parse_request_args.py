from datetime import datetime
import unittest


from hamcrest import *
import pytz
from werkzeug.datastructures import MultiDict

from backdrop.read.api import parse_request_args


class Test_parse_request_args(unittest.TestCase):
    def test_start_at_is_parsed(self):
        request_args = MultiDict([
            ("start_at", "2012-12-12T08:12:43+00:00")])

        args = parse_request_args(request_args)

        assert_that(args['start_at'], is_(
            datetime(2012, 12, 12, 8, 12, 43, tzinfo=pytz.UTC)))

    def test_first_start_at_is_used(self):
        request_args = MultiDict([
            ("start_at", "2012-12-12T08:12:43+00:00"),
            ("start_at", "2012-12-13T08:12:43+00:00"),
        ])

        args = parse_request_args(request_args)

        assert_that(args['start_at'], is_(
            datetime(2012, 12, 12, 8, 12, 43, tzinfo=pytz.UTC)))

    def test_end_at_is_parsed(self):
        request_args = MultiDict([
            ("end_at", "2012-12-12T08:12:43+00:00")])

        args = parse_request_args(request_args)

        assert_that(args['end_at'], is_(
            datetime(2012, 12, 12, 8, 12, 43, tzinfo=pytz.UTC)))

    def test_first_end_at_is_used(self):
        request_args = MultiDict([
            ("end_at", "2012-12-12T08:12:43+00:00"),
            ("end_at", "2012-12-13T08:12:43+00:00"),
        ])

        args = parse_request_args(request_args)

        assert_that(args['end_at'], is_(
            datetime(2012, 12, 12, 8, 12, 43, tzinfo=pytz.UTC)))

    def test_one_filter_by_is_parsed(self):
        request_args = MultiDict([
            ("filter_by", "foo:bar")])

        args = parse_request_args(request_args)

        assert_that(args['filter_by'], has_item(["foo", "bar"]))

    def test_many_filter_by_are_parsed(self):
        request_args = MultiDict([
            ("filter_by", "foo:bar"),
            ("filter_by", "bar:foo")
        ])

        args = parse_request_args(request_args)

        assert_that(args['filter_by'], has_item(["foo", "bar"]))
        assert_that(args['filter_by'], has_item(["bar", "foo"]))

    def test_group_by_is_passed_through_untouched(self):
        request_args = MultiDict([("group_by", "foobar")])

        args = parse_request_args(request_args)

        assert_that(args['group_by'], is_('foobar'))

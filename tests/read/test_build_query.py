from performance_platform.read.api import build_query

import test_helper
import pytz

from datetime import datetime
from unittest import TestCase
from hamcrest import *
from werkzeug import exceptions
from tests.support.aborts_with import aborts_with


class TestBuild_query(TestCase):
    def test_build_query_with_empty_parameters(self):
        assert_that(build_query({}), is_({}))

    def test_build_query_extracts_start_at(self):
        query = build_query({"start_at": "2013-02-25T12:00:30+00:00"})
        assert_that(query, is_({
            "_timestamp": {
                "$gte": datetime(2013, 2, 25, 12, 0, 30, tzinfo=pytz.UTC)
            }
        }))

    def test_build_query_extracts_end_at(self):
        query = build_query({"end_at": "2013-02-25T12:00:30+00:00"})
        assert_that(query, is_({
            "_timestamp": {
                "$lt": datetime(2013, 2, 25, 12, 0, 30, tzinfo=pytz.UTC)
            }
        }))

    def test_build_query_extracts_start_at_and_end_at_correctly(self):
        query = build_query({
            "start_at": "2013-02-10T12:00:30+00:00",
            "end_at": "2013-02-25T12:00:30+00:00"
        })
        expected_query = {
            "_timestamp": {
                "$gte": datetime(2013, 2, 10, 12, 0, 30, tzinfo=pytz.UTC),
                "$lt": datetime(2013, 2, 25, 12, 0, 30, tzinfo=pytz.UTC),
            }
        }
        assert_that(query, is_(expected_query))

    def test_build_query_extracts_filter_by_correctly(self):
        query = build_query({"filter_by": "foo:bar"})
        assert_that(query, is_({"foo": "bar"}))

    def test_reject_invalid_start_at(self):
        assert_that(
            lambda: build_query({"start_at": "i am not a time"}),
            aborts_with(400)
        )

    def test_reject_invalid_end_at(self):
        assert_that(lambda: build_query({"end_at": "foo"}), aborts_with(400))

    def test_reject_filter_with_no_colon(self):
        assert_that(
            lambda: build_query({"filter_by": "bar"}),
            aborts_with(400)
        )

import test_helper
from datetime import datetime
from unittest import TestCase

import pytz

from hamcrest import *

from backdrop.read.api import build_query


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

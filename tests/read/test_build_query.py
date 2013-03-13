from datetime import datetime
from unittest import TestCase

import pytz

from hamcrest import *

from backdrop.read.api import build_query


class TestBuild_query(TestCase):
    def test_build_query_with_empty_parameters(self):
        assert_that(build_query({}), is_({}))

    def test_build_query_extracts_start_at(self):
        timestamp = datetime(2013, 2, 25, 12, 0, 30, tzinfo=pytz.UTC)
        query = build_query({"start_at": timestamp})
        assert_that(query, is_({
            "_timestamp": {
                "$gte": timestamp
            }
        }))

    def test_build_query_extracts_end_at(self):
        timestamp = datetime(2013, 2, 25, 12, 0, 30, tzinfo=pytz.UTC)
        query = build_query({"end_at": timestamp})
        assert_that(query, is_({
            "_timestamp": {
                "$lt": timestamp
            }
        }))

    def test_build_query_extracts_start_at_and_end_at_correctly(self):
        start_at = datetime(2013, 2, 10, 12, 0, 30, tzinfo=pytz.UTC)
        end_at = datetime(2013, 2, 25, 12, 0, 30, tzinfo=pytz.UTC)
        query = build_query({
            "start_at": start_at,
            "end_at": end_at
        })
        expected_query = {
            "_timestamp": {
                "$gte": start_at,
                "$lt": end_at,
            }
        }
        assert_that(query, is_(expected_query))

    def test_build_query_extracts_filter_by_correctly(self):
        query = build_query({"filter_by": [["foo", "bar"]]})
        assert_that(query, is_({"foo": "bar"}))

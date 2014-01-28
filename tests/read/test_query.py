from datetime import datetime
from freezegun import freeze_time
from hamcrest import *
import pytz
from unittest import TestCase

from backdrop.core.timeseries import Day
from backdrop.read.query import Query
from tests.support.test_helpers import d_tz


class TestBuild_query(TestCase):
    def test_build_query_with_start_at(self):
        query = Query.create(start_at=d_tz(2013, 3, 18, 18, 10, 05))
        assert_that(query.to_mongo_query(), is_(
            {"_timestamp": {"$gte": d_tz(2013, 03, 18, 18, 10, 05)}}))

    def test_build_query_with_end_at(self):
        query = Query.create(end_at=d_tz(2012, 3, 17, 17, 10, 6))
        assert_that(query.to_mongo_query(), is_(
            {"_timestamp": {"$lt": d_tz(2012, 3, 17, 17, 10, 6)}}))

    def test_build_query_with_start_and_end_at(self):
        query = Query.create(
            start_at = d_tz(2012, 3, 17, 17, 10, 6),
            end_at = d_tz(2012, 3, 19, 17, 10, 6))
        assert_that(query.to_mongo_query(), is_({
            "_timestamp": {
                "$gte": d_tz(2012, 3, 17, 17, 10, 6),
                "$lt": d_tz(2012, 3, 19, 17, 10, 6)
            }
        }))

    @freeze_time('2014, 1, 09 00:00:00')
    def test_no_end_at_means_now(self):
        query = Query.create(
            period=Day(),
            duration=3,
        )

        assert_that(query.end_at, is_(
            datetime(2014, 1, 9, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_start_at_and_duration(self):
        query = Query.create(
            start_at=d_tz(2014, 1, 9, 0, 0, 0),
            period=Day(),
            duration=3,
        )

        assert_that(query.start_at, is_(
            datetime(2014, 1, 9, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(query.end_at, is_(
            datetime(2014, 1, 12, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_end_at_and_duration(self):
        query = Query.create(
            end_at=d_tz(2014, 1, 11, 0, 0, 0),
            period=Day(),
            duration=3,
        )

        assert_that(query.start_at, is_(
            datetime(2014, 1, 8, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(query.end_at, is_(
            datetime(2014, 1, 11, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_shift_query_forwards(self):
        query = Query.create(
            start_at=d_tz(2014, 1, 9, 0, 0, 0),
            period=Day(),
            duration=6,
        )

        shifted = query.get_shifted_query(5)

        assert_that(shifted.start_at, is_(
            d_tz(2014, 1, 14, 0, 0, 0)))

        assert_that(shifted.end_at, is_(
            d_tz(2014, 1, 20, 0, 0, 0)))

    def test_shift_query_backwards(self):
        query = Query.create(
            start_at=d_tz(2014, 1, 9, 0, 0, 0),
            period=Day(),
            duration=6,
        )

        shifted = query.get_shifted_query(-5)

        assert_that(shifted.start_at, is_(
            d_tz(2014, 1, 4, 0, 0, 0)))

        assert_that(shifted.end_at, is_(
            d_tz(2014, 1, 10, 0, 0, 0)))

    def test_build_query_with_filter(self):
        query = Query.create(filter_by= [[ "foo", "bar" ]])
        assert_that(query.to_mongo_query(), is_({ "foo": "bar" }))

    def test_build_query_with_multiple_filters(self):
        query = Query.create(filter_by= [[ "foo", "bar" ], ["foobar", "yes"]])
        assert_that(query.to_mongo_query(),
                    is_({ "foo": "bar", "foobar": "yes" }))

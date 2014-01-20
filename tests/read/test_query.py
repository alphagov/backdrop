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
    def test_no_date_means_now(self):
        query = Query.create(
            period=Day(),
            delta=3,
        )

        assert_that(query.start_at, is_(
            datetime(2014, 1, 9, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_date_on_boundary_and_positive_delta(self):
        query = Query.create(
            date=d_tz(2014, 1, 9, 0, 0, 0),
            period=Day(),
            delta=3,
        )

        assert_that(query.start_at, is_(
            datetime(2014, 1, 9, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(query.end_at, is_(
            datetime(2014, 1, 12, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_date_on_boundary_and_negative_delta(self):
        query = Query.create(
            date=d_tz(2014, 1, 11, 0, 0, 0),
            period=Day(),
            delta=-3,
        )

        assert_that(query.start_at, is_(
            datetime(2014, 1, 8, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(query.end_at, is_(
            datetime(2014, 1, 11, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_date_off_boundary_and_positive_delta(self):
        query = Query.create(
            date=d_tz(2014, 1, 9, 1, 2, 3),
            period=Day(),
            delta=3,
        )

        assert_that(query.start_at, is_(
            datetime(2014, 1, 10, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(query.end_at, is_(
            datetime(2014, 1, 13, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_date_off_boundary_and_negative_delta(self):
        query = Query.create(
            date=d_tz(2014, 1, 11, 23, 58, 57),
            period=Day(),
            delta=-3,
        )

        assert_that(query.start_at, is_(
            datetime(2014, 1, 8, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(query.end_at, is_(
            datetime(2014, 1, 11, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_get_shifted_resized_with_positive_delta(self):
        query = Query.create(
            date=d_tz(2014, 1, 9, 0, 0, 0),
            period=Day(),
            delta=6,
        )

        shifted = query.get_shifted_resized(12, 5)

        assert_that(shifted.date, is_(
            datetime(2014, 1, 21, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(shifted.delta, is_(5))

        assert_that(shifted.start_at, is_(
            datetime(2014, 1, 21, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(shifted.end_at, is_(
            datetime(2014, 1, 26, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_get_shifted_resized_with_negative_delta(self):
        query = Query.create(
            date=d_tz(2014, 1, 9, 0, 0, 0),
            period=Day(),
            delta=-6,
        )

        shifted = query.get_shifted_resized(12, 5)

        assert_that(shifted.date, is_(
            datetime(2013, 12, 28, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(shifted.delta, is_(-5))

        assert_that(shifted.start_at, is_(
            datetime(2013, 12, 23, 0, 0, 0, tzinfo=pytz.UTC)))

        assert_that(shifted.end_at, is_(
            datetime(2013, 12, 28, 0, 0, 0, tzinfo=pytz.UTC)))

    def test_build_query_with_filter(self):
        query = Query.create(filter_by= [[ "foo", "bar" ]])
        assert_that(query.to_mongo_query(), is_({ "foo": "bar" }))

    def test_build_query_with_multiple_filters(self):
        query = Query.create(filter_by= [[ "foo", "bar" ], ["foobar", "yes"]])
        assert_that(query.to_mongo_query(),
                    is_({ "foo": "bar", "foobar": "yes" }))

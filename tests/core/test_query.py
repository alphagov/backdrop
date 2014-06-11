from datetime import datetime
from freezegun import freeze_time
from hamcrest import assert_that, is_
import pytz
from unittest import TestCase

from backdrop.core.timeseries import Day
from backdrop.core.query import Query

from tests.support.test_helpers import d_tz


class TestBuild_query(TestCase):
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

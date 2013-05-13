from unittest import TestCase
import datetime
from hamcrest import assert_that, is_, contains
from backdrop.core.timeseries import timeseries, WEEK, MONTH
from tests.support.test_helpers import d, d_tz


class TestTimeseries(TestCase):
    def test_returns_a_full_timeseries(self):
        ts = timeseries(start=d_tz(2013, 4, 1),
                        end=d_tz(2013, 4, 15),
                        period=WEEK,
                        data=[],
                        default={"value": 0})

        assert_that(ts, contains(
            {"_start_at": d_tz(2013, 4, 1), "_end_at": d_tz(2013, 4, 8), "value": 0},
            {"_start_at": d_tz(2013, 4, 8), "_end_at": d_tz(2013, 4, 15), "value": 0},
        ))

    def test_adds_data_at_appropriate_places(self):
        data = [
            {"_start_at": d_tz(2013, 4, 1), "_end_at": d_tz(2013, 4, 8), "value": 12}
        ]

        ts = timeseries(start=d_tz(2013, 4, 1),
                        end=d_tz(2013, 4, 15),
                        period=WEEK,
                        data=data,
                        default={"value": 0})

        assert_that(ts, contains(
            {"_start_at": d_tz(2013, 4, 1), "_end_at": d_tz(2013, 4, 8), "value": 12},
            {"_start_at": d_tz(2013, 4, 8), "_end_at": d_tz(2013, 4, 15), "value": 0},
        ))

    def test_start_and_end_are_expanded_to_week_limits(self):
        data = [
            {"_start_at": d_tz(2013, 4, 8), "_end_at": d_tz(2013, 4, 15), "value": 12},
            {"_start_at": d_tz(2013, 4, 15), "_end_at": d_tz(2013, 4, 22), "value": 23}
        ]

        ts = timeseries(start=d_tz(2013, 4, 5),
                        end=d_tz(2013, 4, 25),
                        period=WEEK,
                        data=data,
                        default={"value": 0})

        assert_that(ts, contains(
            {"_start_at": d_tz(2013, 4, 1), "_end_at": d_tz(2013, 4, 8), "value": 0},
            {"_start_at": d_tz(2013, 4, 8), "_end_at": d_tz(2013, 4, 15), "value": 12},
            {"_start_at": d_tz(2013, 4, 15), "_end_at": d_tz(2013, 4, 22), "value": 23},
            {"_start_at": d_tz(2013, 4, 22), "_end_at": d_tz(2013, 4, 29), "value": 0},
        ))


class TestWeek_start(TestCase):
    def test_that_it_returns_previous_monday_for_midweek(self):
        tuesday = datetime.datetime(2013, 4, 9)

        start = WEEK.start(tuesday)

        assert_that(start, is_(datetime.datetime(2013, 4, 8)))

    def test_that_it_truncates_the_time_part(self):
        tuesday = datetime.datetime(2013, 4, 9, 23, 12)

        start = WEEK.start(tuesday)

        assert_that(start, is_(datetime.datetime(2013, 4, 8)))

    def test_that_it_returns_the_same_day_for_monday(self):
        monday = datetime.datetime(2013, 4, 8, 23, 12)

        start = WEEK.start(monday)

        assert_that(start, is_(datetime.datetime(2013, 4, 8)))

    def test_that_it_returns_the_same_day_for_monday_midnight(self):
        monday = datetime.datetime(2013, 4, 8, 0, 0)

        start = WEEK.start(monday)

        assert_that(start, is_(datetime.datetime(2013, 4, 8)))


class TestWeek_end(TestCase):
    def test_that_it_returns_next_monday_for_midweek(self):
        tuesday = datetime.datetime(2013, 4, 9)

        end = WEEK.end(tuesday)

        assert_that(end, is_(datetime.datetime(2013, 4, 15)))

    def test_that_it_truncates_the_time_part(self):
        tuesday = datetime.datetime(2013, 4, 9, 23, 12)

        end = WEEK.end(tuesday)

        assert_that(end, is_(datetime.datetime(2013, 4, 15)))

    def test_that_it_returns_the_same_day_for_monday_midnight(self):
        monday = datetime.datetime(2013, 4, 8, 0, 0)

        end = WEEK.end(monday)

        assert_that(end, is_(datetime.datetime(2013, 4, 8)))

    def test_that_it_returns_the_next_monday_for_monday_after_midnight(self):
        monday = datetime.datetime(2013, 4, 8, 23, 12)

        end = WEEK.end(monday)

        assert_that(end, is_(datetime.datetime(2013, 4, 15)))


class TestWeek_range(TestCase):
    def test_that_it_produces_a_sequence_of_weekly_time_periods(self):
        range = WEEK.range(d_tz(2013, 4, 1), d_tz(2013, 4, 15))

        assert_that(list(range), contains(
            (d_tz(2013, 4, 1), d_tz(2013, 4, 8)),
            (d_tz(2013, 4, 8), d_tz(2013, 4, 15))
        ))

    def test_that_it_expands_the_limits_of_the_range_if_midweek(self):
        range = WEEK.range(d_tz(2013, 4, 3), d_tz(2013, 4, 19))

        assert_that(list(range), contains(
            (d_tz(2013, 4, 1), d_tz(2013, 4, 8)),
            (d_tz(2013, 4, 8), d_tz(2013, 4, 15)),
            (d_tz(2013, 4, 15), d_tz(2013, 4, 22))
        ))


class TestMonth_start(TestCase):
    def test_that_it_returns_first_of_current_month_for_midmonth(self):
        some_datetime = d(2013, 4, 9)

        start = MONTH.start(some_datetime)

        assert_that(start, is_(d(2013, 4, 1)))

    def test_that_it_truncates_the_time_part(self):
        some_datetime = d(2013, 5, 7, 10, 12, 13)

        start = MONTH.start(some_datetime)

        assert_that(start.hour, is_(0))
        assert_that(start.minute, is_(0))
        assert_that(start.second, is_(0))
        assert_that(start.microsecond, is_(0))

    def test_that_it_returns_same_day_for_first_of_month(self):
        some_datetime = d(2013, 12, 1, 12, 32, 34)

        start = MONTH.start(some_datetime)

        assert_that(start, is_(d(2013, 12, 1)))

    def test_that_it_returns_same_day_for_first_of_month_midnight(self):
        some_datetime = datetime.datetime(
            year=2013, month=11, day=1, hour=0, minute=0, second=0,
            microsecond=0)

        start = MONTH.start(some_datetime)

        assert_that(start, is_(some_datetime))


class TestMonth_end(object):
    def test_that_it_returns_the_end_of_the_current_month(self):
        some_datetime = d(2013, 10, 4, 10, 23, 43)
        some_other_datetime = d(2013, 10, 4)

        end = MONTH.end(some_datetime)
        other_end = MONTH.end(some_other_datetime)

        assert_that(end, is_(d(2013, 11, 1)))
        assert_that(other_end, is_(d(2013, 11, 1)))

    def test_that_it_truncates_the_time_part(self):
        some_datetime = d(2013, 4, 9, 23, 12)

        end = MONTH.end(some_datetime)

        assert_that(end, is_(d(2013, 5, 1)))

    def test_that_it_returns_the_same_month_for_month_boundary_midnight(self):
        some_datetime = d(2013, 5, 1, 0, 0)

        end = MONTH.end(some_datetime)

        assert_that(end, is_(d(2013, 5, 1)))

    def test_that_it_returns_the_next_month_for_boundary_after_midnight(self):
        some_datetime = d(2013, 5, 1, 0, 12)

        end = MONTH.end(some_datetime)

        assert_that(end, is_(d(2013, 6, 1)))


class TestMonth_range(TestCase):
    def test_that_it_produces_a_sequence_of_monthly_time_periods(self):
        range = MONTH.range(d_tz(2013, 4, 1), d_tz(2013, 6, 1))

        assert_that(list(range), contains(
            (d_tz(2013, 4, 1), d_tz(2013, 5, 1)),
            (d_tz(2013, 5, 1), d_tz(2013, 6, 1))
        ))

    def test_that_it_expands_the_limits_of_the_range_if_midmonth(self):
        range = MONTH.range(d_tz(2013, 4, 3), d_tz(2013, 5, 19))

        assert_that(list(range), contains(
            (d_tz(2013, 4, 1), d_tz(2013, 5, 1)),
            (d_tz(2013, 5, 1), d_tz(2013, 6, 1)),
        ))

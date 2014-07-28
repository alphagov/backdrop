from unittest import TestCase
import datetime
from hamcrest import assert_that, is_, contains
from backdrop.core.timeseries import timeseries, HOUR, DAY, WEEK, MONTH, QUARTER, YEAR
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


class TestDay(TestCase):
    def test_that_returns_the_beginning_of_the_current_day(self):
        some_datetime = d(2013, 10, 4, 10, 23, 43)

        start = DAY.start(some_datetime)

        assert_that(start, is_(d(2013, 10, 4, 0, 0, 0)))

    def test_that_midday_is_not_a_valid_start_at(self):
        naughty_starttime = d(2013, 10, 18, 12, 00)

        assert_that(DAY.valid_start_at(naughty_starttime), is_(False))

    def test_that_beginning_of_the_day_is_a_valid_start_at(self):
        lovely_starttime = d(2013, 10, 18, 00, 00)

        assert_that(DAY.valid_start_at(lovely_starttime), is_(True))

    def test_that_end_of_the_day_is_the_beginning_of_the_next_day(self):
        late_in_the_day = d(2013, 10, 18, 21, 00)

        assert_that(DAY.end(late_in_the_day), is_(d(2013, 10, 19, 00, 00)))

    def test_that_a_range_of_one_week_gives_us_seven_days(self):
        range = DAY.range(d_tz(2013, 4, 3), d_tz(2013, 4, 10))

        assert_that(list(range), contains(
            (d_tz(2013, 4, 3), d_tz(2013, 4, 4)),
            (d_tz(2013, 4, 4), d_tz(2013, 4, 5)),
            (d_tz(2013, 4, 5), d_tz(2013, 4, 6)),
            (d_tz(2013, 4, 6), d_tz(2013, 4, 7)),
            (d_tz(2013, 4, 7), d_tz(2013, 4, 8)),
            (d_tz(2013, 4, 8), d_tz(2013, 4, 9)),
            (d_tz(2013, 4, 9), d_tz(2013, 4, 10))
        ))


class TestHour(TestCase):
    def test_that_returns_the_beginning_of_the_current_hour(self):
        some_datetime = d(2013, 10, 4, 10, 23, 43)

        start = HOUR.start(some_datetime)

        assert_that(start, is_(d(2013, 10, 4, 10, 0, 0)))

    def test_that_middle_of_the_hour_is_not_a_valid_start_at(self):
        middle_of_the_hour = d(2013, 10, 18, 12, 31)

        assert_that(HOUR.valid_start_at(middle_of_the_hour), is_(False))

    def test_that_beginning_of_the_hour_is_a_valid_start_at(self):
        beginning_of_the_hour = d(2013, 10, 18, 12, 0)

        assert_that(HOUR.valid_start_at(beginning_of_the_hour), is_(True))

    def test_that_returns_the_end_of_the_current_hour(self):
        some_datetime = d(2013, 10, 4, 10, 23, 43)

        end = HOUR.end(some_datetime)

        assert_that(end, is_(d(2013, 10, 4, 11, 0, 0)))

    def test_that_a_range_of_five_hours_gives_us_five_data_points(self):
        range = HOUR.range(d_tz(2013, 4, 3, 12), d_tz(2013, 4, 3, 17))

        assert_that(list(range), contains(
            (d_tz(2013, 4, 3, 12), d_tz(2013, 4, 3, 13)),
            (d_tz(2013, 4, 3, 13), d_tz(2013, 4, 3, 14)),
            (d_tz(2013, 4, 3, 14), d_tz(2013, 4, 3, 15)),
            (d_tz(2013, 4, 3, 15), d_tz(2013, 4, 3, 16)),
            (d_tz(2013, 4, 3, 16), d_tz(2013, 4, 3, 17))
        ))


class TestQuarter(TestCase):
    def test_that_returns_the_beginning_of_the_first_quarter(self):
        some_datetime = d(2013, 1, 20, 0, 23, 43)

        assert_that(QUARTER.start(some_datetime), is_(d(2013, 1, 1, 0, 0, 0)))

    def test_that_returns_the_beginning_of_the_second_quarter(self):
        some_datetime = d(2013, 5, 20, 0, 23, 43)

        assert_that(QUARTER.start(some_datetime), is_(d(2013, 4, 1, 0, 0, 0)))

    def test_that_returns_the_beginning_of_the_third_quarter(self):
        some_datetime = d(2013, 9, 20, 0, 23, 43)

        assert_that(QUARTER.start(some_datetime), is_(d(2013, 7, 1, 0, 0, 0)))

    def test_that_returns_the_beginning_of_the_fourth_quarter(self):
        some_datetime = d(2013, 12, 4, 10, 23, 43)

        assert_that(QUARTER.start(some_datetime), is_(d(2013, 10, 1, 0, 0, 0)))

    def test_that_beginning_of_quarters_are_valid(self):
        first_quarter = d(2013, 1, 1, 0, 0, 0)
        second_quarter = d(2013, 4, 1, 0, 0, 0)
        third_quarter = d(2013, 7, 1, 0, 0, 0)
        fourth_quarter = d(2013, 10, 1, 0, 0, 0)

        assert_that(QUARTER.valid_start_at(first_quarter), is_(True))
        assert_that(QUARTER.valid_start_at(second_quarter), is_(True))
        assert_that(QUARTER.valid_start_at(third_quarter), is_(True))
        assert_that(QUARTER.valid_start_at(fourth_quarter), is_(True))

    def test_that_middle_of_quarters_are_invalid(self):
        middle_first_quarter = d(2013, 1, 10, 0, 0, 0)
        middle_second_quarter = d(2013, 4, 15, 0, 0, 0)
        middle_third_quarter = d(2013, 7, 20, 0, 0, 0)
        middle_fourth_quarter = d(2013, 10, 13, 0, 0, 0)

        assert_that(QUARTER.valid_start_at(middle_first_quarter), is_(False))
        assert_that(QUARTER.valid_start_at(middle_second_quarter), is_(False))
        assert_that(QUARTER.valid_start_at(middle_third_quarter), is_(False))
        assert_that(QUARTER.valid_start_at(middle_fourth_quarter), is_(False))

    def test_end_of_quarter_is_beginning_of_next_quarter(self):
        first_quarter = d(2013, 1, 1, 0, 0, 0)
        second_quarter = d(2013, 4, 1, 0, 0, 0)
        third_quarter = d(2013, 7, 1, 0, 0, 0)
        fourth_quarter = d(2013, 10, 1, 0, 0, 0)
        first_quarter_2014 = d(2014, 1, 1, 0, 0, 0)

        assert_that(QUARTER.end(first_quarter.replace(hour=1)), is_(second_quarter))
        assert_that(QUARTER.end(second_quarter.replace(hour=1)), is_(third_quarter))
        assert_that(QUARTER.end(third_quarter.replace(hour=1)), is_(fourth_quarter))
        assert_that(QUARTER.end(fourth_quarter.replace(hour=1)), is_(first_quarter_2014))

    def test_range_of_quarters(self):
        range = QUARTER.range(d_tz(2012, 10, 1), d_tz(2013, 12, 30))

        assert_that(list(range), contains(
            (d_tz(2012, 10, 1), d_tz(2013, 1, 1)),
            (d_tz(2013, 1, 1),  d_tz(2013, 4, 1)),
            (d_tz(2013, 4, 1),  d_tz(2013, 7, 1)),
            (d_tz(2013, 7, 1),  d_tz(2013, 10, 1)),
            (d_tz(2013, 10, 1), d_tz(2014, 1, 1))
        ))


class TestYear(TestCase):
    def test_year_start_returns_the_beginning_of_the_given_year(self):
        some_datetime = d(2013, 1, 20, 0, 23, 43)

        assert_that(YEAR.start(some_datetime), is_(d(2013, 1, 1, 0, 0, 0)))

    def test_start_of_year_is_valid(self):
        assert_that(YEAR.valid_start_at(d(2013, 1, 1, 0, 0, 0)), is_(True))

    def test_start_of_year_plus_second_is_invalid(self):
        assert_that(YEAR.valid_start_at(d(2013, 1, 1, 0, 0, 1)), is_(False))

    def test_start_of_year_plus_minute_is_invalid(self):
        assert_that(YEAR.valid_start_at(d(2013, 1, 1, 0, 1, 0)), is_(False))

    def test_start_of_year_plus_hour_is_invalid(self):
        assert_that(YEAR.valid_start_at(d(2013, 1, 1, 1, 0, 0)), is_(False))

    def test_start_of_year_plus_day_is_invalid(self):
        assert_that(YEAR.valid_start_at(d(2013, 1, 2, 0, 0, 0)), is_(False))

    def test_start_of_year_plus_month_is_invalid(self):
        assert_that(YEAR.valid_start_at(d(2013, 2, 1, 0, 0, 0)), is_(False))

    def test_end_of_year_is_beginning_of_next_year(self):
        some_datetime = d(2013, 10, 4, 10, 23, 43)

        end = YEAR.end(some_datetime)

        assert_that(end, is_(d(2014, 1, 1, 0, 0, 0)))

    def test_that_a_range_of_five_years_gives_us_five_data_points(self):
        range = YEAR.range(d_tz(2010, 1, 1), d_tz(2015, 1, 1))

        assert_that(list(range), contains(
            (d_tz(2010, 1, 1), d_tz(2011, 1, 1)),
            (d_tz(2011, 1, 1), d_tz(2012, 1, 1)),
            (d_tz(2012, 1, 1), d_tz(2013, 1, 1)),
            (d_tz(2013, 1, 1), d_tz(2014, 1, 1)),
            (d_tz(2014, 1, 1), d_tz(2015, 1, 1)),
        ))

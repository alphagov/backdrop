from unittest import TestCase
import datetime
from hamcrest import assert_that, is_
from backdrop.core.timeseries import week_start, week_end


class TestWeek_start(TestCase):
    def test_that_it_returns_previous_monday_for_midweek(self):
        tuesday = datetime.datetime(2013, 4, 9)

        start = week_start(tuesday)

        assert_that(start, is_(datetime.datetime(2013, 4, 8)))

    def test_that_it_truncates_the_time_part(self):
        tuesday = datetime.datetime(2013, 4, 9, 23, 12)

        start = week_start(tuesday)

        assert_that(start, is_(datetime.datetime(2013, 4, 8)))

    def test_that_it_returns_the_same_day_for_monday(self):
        monday = datetime.datetime(2013, 4, 8, 23, 12)

        start = week_start(monday)

        assert_that(start, is_(datetime.datetime(2013, 4, 8)))

    def test_that_it_returns_the_same_day_for_monday_midnight(self):
        monday = datetime.datetime(2013, 4, 8, 0, 0)

        start = week_start(monday)

        assert_that(start, is_(datetime.datetime(2013, 4, 8)))


class TestWeek_end(TestCase):
    def test_that_it_returns_next_monday_for_midweek(self):
        tuesday = datetime.datetime(2013, 4, 9)

        end = week_end(tuesday)

        assert_that(end, is_(datetime.datetime(2013, 4, 15)))

    def test_that_it_truncates_the_time_part(self):
        tuesday = datetime.datetime(2013, 4, 9, 23, 12)

        end = week_end(tuesday)

        assert_that(end, is_(datetime.datetime(2013, 4, 15)))

    def test_that_it_returns_the_same_day_for_monday_midnight(self):
        monday = datetime.datetime(2013, 4, 8, 0, 0)

        end = week_end(monday)

        assert_that(end, is_(datetime.datetime(2013, 4, 8)))

    def test_that_it_returns_the_next_monday_for_monday_after_midnight(self):
        monday = datetime.datetime(2013, 4, 8, 23, 12)

        end = week_end(monday)

        assert_that(end, is_(datetime.datetime(2013, 4, 15)))

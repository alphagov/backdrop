from datetime import timedelta, time
import time as _time
from dateutil.relativedelta import relativedelta, MO
import pytz


class Period(object):
    @property
    def delta(self):
        return self._delta

    @property
    def start_at_key(self):
        return "_%s_start_at" % self.name

    def _is_boundary(self, timestamp):
        return self.valid_start_at(timestamp) \
            and self._is_start_of_day(timestamp)

    def _is_start_of_day(self, timestamp):
        return timestamp.time() == time(0, 0, 0, 0)

    def end(self, timestamp):
        if self._is_boundary(timestamp):
                return timestamp
        return self.start(timestamp + self._delta)

    def range(self, start, end):
        _start = self.start(start).replace(tzinfo=pytz.UTC)
        _end = self.end(end).replace(tzinfo=pytz.UTC)
        while (_start < _end):
            yield (_start, _start + self._delta)
            _start += self._delta


class Hour(Period):
    def __init__(self):
        self.name = "hour"
        self._delta = timedelta(hours=1)

    def _is_boundary(self, timestamp):
        return self.valid_start_at(timestamp)

    def start(self, timestamp):
        return timestamp.replace(minute=0, second=0, microsecond=0)

    def valid_start_at(self, timestamp):
        return timestamp.time() == time(timestamp.hour, 0, 0, 0)


class Day(Period):
    def __init__(self):
        self.name = "day"
        self._delta = timedelta(days=1)

    def start(self, timestamp):
        return _truncate_time(timestamp)

    def valid_start_at(self, timestamp):
        return self._is_start_of_day(timestamp)


class Week(Period):
    def __init__(self):
        self.name = "week"
        self._delta = timedelta(days=7)

    def start(self, timestamp):
        return _truncate_time(timestamp) + relativedelta(weekday=MO(-1))

    def valid_start_at(self, timestamp):
        return timestamp.weekday() is 0


class Month(Period):
    def __init__(self):
        self.name = "month"
        self._delta = relativedelta(months=1)

    def start(self, timestamp):
        return timestamp.replace(day=1, hour=0, minute=0,
                                 second=0, microsecond=0)

    def valid_start_at(self, timestamp):
        return timestamp.day == 1


class Quarter(Period):
    def __init__(self):
        self.name = "quarter"
        self._delta = relativedelta(months=3)
        self.quarter_starts = [10, 7, 4, 1]

    def start(self, timestamp):
        quarter_month = next(quarter for quarter in self.quarter_starts
                             if timestamp.month >= quarter)

        return timestamp.replace(month=quarter_month, day=1, hour=0, minute=0,
                                 second=0, microsecond=0)

    def valid_start_at(self, timestamp):
        return timestamp.day == 1 and timestamp.month in self.quarter_starts


HOUR = Hour()
DAY = Day()
WEEK = Week()
MONTH = Month()
QUARTER = Quarter()
PERIODS = [HOUR, DAY, WEEK, MONTH, QUARTER]


def parse_period(period_name):
    for period in PERIODS:
        if period.name == period_name:
            return period


def _time_to_index(dt):
    return _time.mktime(dt.replace(tzinfo=pytz.utc).timetuple())


def timeseries(start, end, period, data, default):
    data_by_start_at = _index_by_start_at(data)

    def entry(start, end):
        time_index = _time_to_index(start)
        if time_index in data_by_start_at:
            return data_by_start_at[time_index]
        else:
            return _merge(default, _period_limits(start, end))
    return [entry(start, end) for start, end in period.range(start, end)]


def _period_limits(start, end):
    return {
        "_start_at": start,
        "_end_at": end
    }


def _index_by_start_at(data):
    return dict((_time_to_index(d["_start_at"]), d) for d in data)


def _period_range(start, stop, period):
    while start < stop:
        yield (start, start + period)
        start += period


def _merge(first, second):
    return dict(first.items() + second.items())


def _truncate_time(datetime):
    return datetime.replace(hour=0, minute=0, second=0, microsecond=0)

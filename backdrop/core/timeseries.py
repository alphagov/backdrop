from datetime import timedelta, time
from dateutil.relativedelta import relativedelta, MO


WEEK = timedelta(days=7)


def timeseries(start, end, period, data, default):
    data_by_start_at = _index_by_start_at(data)

    def entry(start, end):
        if start in data_by_start_at:
            return data_by_start_at[start]
        else:
            return _merge(default, _period_limits(end, start))

    delta = _period_to_timedelta(period)
    period_range = _period_range(week_start(start), week_end(end), delta)

    return [entry(start, end) for start, end in period_range]


def week_start(datetime):
    return _truncate_time(datetime) + relativedelta(weekday=MO(-1))


def week_end(datetime):
    if _monday_midnight(datetime):
        return datetime
    return week_start(datetime) + timedelta(days=7)


def _period_limits(end, start):
    return {
        "_start_at": start,
        "_end_at": end
    }


def _index_by_start_at(data):
    return dict((d["_start_at"], d) for d in data)


def _period_range(start, stop, period):
    while start < stop:
        yield (start, start + period)
        start += period


def _merge(first, second):
    return dict(first.items() + second.items())


def _period_to_timedelta(period):
    return period


def _monday_midnight(datetime):
    return datetime.weekday() == 0 and datetime.time() == time(0, 0, 0, 0)


def _truncate_time(datetime):
    return datetime.replace(hour=0, minute=0, second=0, microsecond=0)

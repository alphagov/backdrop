from datetime import timedelta, time
from dateutil.relativedelta import relativedelta, MO


def timeseries(start, end, data, period, default):
    pass


def week_start(datetime):
    return _truncate_time(datetime) + relativedelta(weekday=MO(-1))


def week_end(datetime):
    if _monday_midnight(datetime):
        return datetime
    return week_start(datetime) + timedelta(days=7)


def _monday_midnight(datetime):
    return datetime.weekday() == 0 and datetime.time() == time(0, 0, 0, 0)


def _truncate_time(datetime):
    return datetime.replace(hour=0, minute=0, second=0, microsecond=0)

import datetime
from dateutil import parser
import pytz


def now():
    return datetime.datetime.now(pytz.UTC)


def parse_time_as_utc(time_string):
    if isinstance(time_string, datetime.datetime):
        time = time_string
    else:
        time = parser.parse(time_string)

    return as_utc(time)


def as_utc(dt):
    if dt.tzinfo is None:
        return utc(dt)
    else:
        return dt.astimezone(pytz.utc)


def utc(dt):
    return dt.replace(tzinfo=pytz.UTC)

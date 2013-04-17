import datetime
import pytz


def now():
    return datetime.datetime.now(pytz.UTC)

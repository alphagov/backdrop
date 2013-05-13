from dateutil import parser
import pytz

from backdrop.core.timeseries import WEEK


class Record(object):
    def __init__(self, data):
        self.data = data
        self.meta = {}

        if "_timestamp" in self.data:
            self.meta['_week_start_at'] = WEEK.start(self.data['_timestamp'])

    def to_mongo(self):
        return dict(
            self.data.items() + self.meta.items()
        )

    def __eq__(self, other):
        if not isinstance(other, Record):
            return False
        if self.data != other.data:
            return False
        if self.meta != other.meta:
            return False
        return True


def parse(data):
    if '_timestamp' in data:
        data['_timestamp'] = _time_string_to_utc_datetime(data['_timestamp'])
    return Record(data)


def _time_string_to_utc_datetime(time_string):
    time = parser.parse(time_string)
    return time.astimezone(pytz.utc)

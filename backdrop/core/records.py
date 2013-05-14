from dateutil import parser
import pytz
from backdrop.core.timeseries import WEEK
from backdrop.core.validation import ValidationError, validate_record_data


class Record(object):

    def __init__(self, data):
        result = validate_record_data(data)
        if not result.is_valid:
            raise ValidationError(result.message)

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


def parse(datum):
    if '_timestamp' in datum:
        try:
            datum['_timestamp'] = _time_string_to_utc_datetime(
                datum['_timestamp'])
        except ValueError:
            raise ValidationError(
                '_timestamp is not a valid timestamp, it must be ISO8601')

    return Record(datum)


def parse_all(data):
    return [parse(datum) for datum in data]


def _time_string_to_utc_datetime(time_string):
    time = parser.parse(time_string)
    return time.astimezone(pytz.utc)

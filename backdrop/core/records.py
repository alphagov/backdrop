from backdrop.core.timeseries import WEEK, MONTH
from backdrop.core.timeutils import parse_time_as_utc
from backdrop.core.validation import validate_record_data
from .errors import ParseError, ValidationError


class Record(object):
    def __init__(self, data):
        result = validate_record_data(data)
        if not result.is_valid:
            raise ValidationError(result.message)

        self.data = data
        self.meta = {}

        if "_timestamp" in self.data:
            self.meta['_week_start_at'] = WEEK.start(self.data['_timestamp'])
            self.meta['_month_start_at'] = MONTH.start(self.data['_timestamp'])

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
            datum['_timestamp'] = parse_time_as_utc(
                datum['_timestamp'])
        except ValueError:
            raise ParseError(
                '_timestamp is not a valid timestamp, it must be ISO8601')

    return Record(datum)


def parse_all(data):
    return [parse(datum) for datum in data]

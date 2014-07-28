from base64 import b64encode

from backdrop.core.timeseries import PERIODS
from backdrop.core.timeutils import parse_time_as_utc
from backdrop.core.validation import validate_record_data
from .errors import ParseError, ValidationError


def add_auto_ids(records, auto_ids):
    """Adds automatically generated IDs to a list of records
    """
    if auto_ids:
        return (_add_auto_id(record, auto_ids) for record in records)
    else:
        return records


def _add_auto_id(record, auto_ids):
    """Adds an automatically generated ID to a record

    >>> record = {'foo': 'foo', 'bar': 'bar'}
    >>> _add_auto_id(record, ['foo'])
    {'foo': 'foo', 'bar': 'bar', '_id': 'Zm9v'}
    >>> _add_auto_id(record, ['foo', 'bar'])
    {'foo': 'foo', 'bar': 'bar', '_id': 'Zm9vLmJhcg=='}
    """
    record['_id'] = _generate_auto_id(record, auto_ids)

    return record


def _generate_auto_id(record, auto_id_keys):
    """Generates an automatic ID from a set of fields in a record

    >>> _generate_auto_id({'foo':'foo'}, ['foo'])
    'Zm9v'
    >>> _generate_auto_id({'foo':'foo'}, ['bar'])
    Traceback (most recent call last):
        ...
    ValidationError: The following required fields are missing: bar
    """
    missing_keys = set(auto_id_keys) - set(record.keys())
    if len(missing_keys) > 0:
        raise ValidationError(
            "The following required fields are missing: {}".format(
                ', '.join(missing_keys)))

    return b64encode('.'.join(
        record[key] for key in auto_id_keys))


def parse_timestamp(record):
    """Parses a timestamp in a record

    >>> parse_timestamp({'_timestamp': '2012-12-12T00:00:00'})
    {'_timestamp': datetime.datetime(2012, 12, 12, 0, 0, tzinfo=<UTC>)}
    >>> parse_timestamp({})
    {}
    >>> parse_timestamp({'_timestamp': 'invalid'})
    Traceback (most recent call last):
        ...
    ParseError: _timestamp is not a valid timestamp, it must be ISO8601
    """
    if '_timestamp' in record:
        try:
            record['_timestamp'] = parse_time_as_utc(record['_timestamp'])
        except (TypeError, ValueError):
            raise ParseError(
                '_timestamp is not a valid timestamp, it must be ISO8601')

    return record


def add_period_keys(record):
    """Adds period start fields to a record

    Add a field for each of the periods in timeseries.PERIODS

    >>> record = add_period_keys(
    ...   parse_timestamp({'_timestamp': '2012-12-12T12:12:00'}))
    >>> record['_hour_start_at']
    datetime.datetime(2012, 12, 12, 12, 0, tzinfo=<UTC>)
    >>> record['_day_start_at']
    datetime.datetime(2012, 12, 12, 0, 0, tzinfo=<UTC>)
    >>> record['_week_start_at']
    datetime.datetime(2012, 12, 10, 0, 0, tzinfo=<UTC>)
    >>> record['_month_start_at']
    datetime.datetime(2012, 12, 1, 0, 0, tzinfo=<UTC>)
    >>> record['_quarter_start_at']
    datetime.datetime(2012, 10, 1, 0, 0, tzinfo=<UTC>)
    >>> record['_year_start_at']
    datetime.datetime(2012, 1, 1, 0, 0, tzinfo=<UTC>)
    """
    if '_timestamp' in record:
        for period in PERIODS:
            record[period.start_at_key] = period.start(
                record['_timestamp'])

    return record


def validate_record(record):
    """Validate a record

    Raises a ValidationError if the record is invalid, otherwise returns
    the record
    """
    # TODO: refactor this
    result = validate_record_data(record)
    if not result.is_valid:
        raise ValidationError(result.message)
    return record

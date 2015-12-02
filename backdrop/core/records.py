# -*- coding: utf-8 -*-

from base64 import b64encode

from backdrop.core.timeseries import PERIODS
from backdrop.core.timeutils import parse_time_as_utc
from backdrop.core.validation import validate_record_data
from .errors import ValidationError


def add_auto_ids(records, auto_ids):
    """Adds automatically generated IDs to a list of records
    """
    # Max one error per record set if the data comes from a csv.
    # If the data comes from elsewhere, some records may be missing id fields
    # and others may not but we won't worry about this for now.
    # We'll catch a single exception for the set, when we do location we can
    # set it to the whole document.
    try:
        if auto_ids:
            return ([_add_auto_id(record, auto_ids) for record in records],
                    [])
        else:
            return (records, [])
    except ValidationError as e:
        return (records, [e.message])


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
    ValidationError: The following required id fields are missing: bar
    """
    missing_keys = set(auto_id_keys) - set(record.keys())
    if len(missing_keys) > 0:
        raise ValidationError(
            "The following required id fields are missing: {}".format(
                ', '.join(missing_keys)))

    return b64encode('.'.join(
        str(record[key]) for key in auto_id_keys))


def parse_timestamps(record):
    """Parses a timestamp in a record

    >>> parse_timestamps({'_timestamp': '2012-12-12T00:00:00'})
    ({'_timestamp': datetime.datetime(2012, 12, 12, 0, 0, tzinfo=<UTC>)}, None)
    >>> parse_timestamps({'_start_at': '2012-12-12T00:00:00'})
    ({'_start_at': datetime.datetime(2012, 12, 12, 0, 0, tzinfo=<UTC>)}, None)
    >>> parse_timestamps({'_end_at': '2012-12-12T00:00:00'})
    ({'_end_at': datetime.datetime(2012, 12, 12, 0, 0, tzinfo=<UTC>)}, None)
    >>> parse_timestamps({})
    ({}, None)
    >>> record, error = parse_timestamps({'_timestamp': 'invalid'})
    >>> record
    {'_timestamp': 'invalid'}
    >>> error
    '_timestamp is not a valid timestamp, it must be ISO8601'
    >>> record, error = parse_timestamps({'_start_at': 'invalid'})
    >>> record
    {'_start_at': 'invalid'}
    >>> error
    '_start_at is not a valid timestamp, it must be ISO8601'
    """
    error = None
    if '_timestamp' in record:
        try:
            record['_timestamp'] = parse_time_as_utc(record['_timestamp'])
        except (TypeError, ValueError):
            error = '_timestamp is not a valid timestamp, it must be ISO8601'

    if '_start_at' in record:
        try:
            record['_start_at'] = parse_time_as_utc(record['_start_at'])
        except (TypeError, ValueError):
            error = '_start_at is not a valid timestamp, it must be ISO8601'

    if '_end_at' in record:
        try:
            record['_end_at'] = parse_time_as_utc(record['_end_at'])
        except (TypeError, ValueError):
            error = '_end_at is not a valid timestamp, it must be ISO8601'

    return (record, error)


def add_period_keys(record):
    """Adds period start fields to a record

    Add a field for each of the periods in timeseries.PERIODS

    >>> record = add_period_keys(
    ...   parse_timestamps({'_timestamp': '2012-12-12T12:12:00'})[0])
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
        return result.message
    return None


def encode_unicode_records(records):
    return [encode_unicode_characters(record) for record in records]


def encode_unicode_characters(record):
    """Encodes unicode characters in a record
    >>> encode_unicode_characters({'name_1': u'PortimÃ£o'})
    {'name_1': 'Portim\\xc3\\x83\\xc2\\x83\\xc3\\x82\\xc2\\xa3o'}
    >>> encode_unicode_characters({'name_2': u'DÃ¼sseldorf'})
    {'name_2': 'D\\xc3\\x83\\xc2\\x83\\xc3\\x82\\xc2\\xbcsseldorf'}
    >>> encode_unicode_characters({'name_3': u'São Tomé and Príncipe'})
    {'name_3': 'S\\xc3\\x83\\xc2\\xa3o Tom\\xc3\\x83\\xc2\\xa9 and Pr\\xc3\\x83\\xc2\\xadncipe'}
    >>> encode_unicode_characters({'name_4': u'Adjudicator’s'})
    {'name_4': 'Adjudicator\\xc3\\xa2\\xc2\\x80\\xc2\\x99s'}
    >>> encode_unicode_characters({'name_5': u'Reject – Dual'})
    {'name_5': 'Reject \\xc3\\xa2\\xc2\\x80\\xc2\\x93 Dual'}
    >>> encode_unicode_characters({'_timestamp': '12-12-2012 00:00:00'})
    {'_timestamp': '12-12-2012 00:00:00'}
    """

    for key, value in record.iteritems():
        if isinstance(value, basestring):
            record[key] = value.encode('utf-8', 'xmlcharrefreplace')
    return record

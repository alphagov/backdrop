"""Validators and validation related functions and types.

Validators should validate a specific type of thing and return a boolean.
App specific validation functions combine validators and return a
ValidationResult object.
"""
from collections import namedtuple
import re
from dateutil import parser

RESERVED_KEYWORDS = (
    '_timestamp',
    '_start_at',
    '_end_at',
    '_id'
)
VALID_KEYWORD = re.compile('^[a-z0-9_\.-]+$')
VALID_BUCKET_NAME = re.compile('^[a-z0-9\.-][a-z0-9_\.-]*$')


def _is_real_date(value):
    try:
        parser.parse(value)
        return True
    except ValueError:
        return False


def _is_valid_format(value):
    time_pattern = re.compile(
        "[0-9]{4}-[0-9]{2}-[0-9]{2}"
        "T[0-9]{2}:[0-9]{2}:[0-9]{2}"
        "(?:[+-][0-9]{2}:?[0-9]{2}|Z)"
    )
    return bool(time_pattern.match(value))


def value_is_valid_datetime_string(value):
    return _is_valid_format(value) and _is_real_date(value)


def value_is_valid(value):
    return isinstance(value, (int, basestring, bool))


def key_is_valid(key):
    key = key.lower()
    if not key:
        return False
    if key[0] == '_':
        if key in RESERVED_KEYWORDS:
            return True
    else:
        if VALID_KEYWORD.match(key):
            return True
    return False


def bucket_is_valid(bucket_name):
    if VALID_BUCKET_NAME.match(bucket_name):
        return True
    return False


def value_is_valid_id(value):
    if not isinstance(value, basestring):
        return False
    if re.compile('\s').search(value):
        return False
    return len(value) > 0


ValidationResult = namedtuple('ValidationResult', 'is_valid message')


def valid():
    return ValidationResult(True, '')


def invalid(message):
    return ValidationResult(False, message)

from contextlib import contextmanager
import datetime
from dateutil import parser
from hamcrest.core.base_matcher import BaseMatcher
import json
import os
from os.path import dirname, join as pjoin
import pytz
import re


class IsResponseWithStatus(BaseMatcher):
    def __init__(self, expected_status):
        self.expected_status = expected_status

    def _matches(self, response):
        return response.status_code == self.expected_status

    def describe_to(self, description):
        description.append_text(
            "response with status code %d" % self.expected_status)


def has_status(status_code):
    return IsResponseWithStatus(status_code)


def is_bad_request():
    return has_status(400)


def is_unauthorized():
    return has_status(401) and has_header('WWW-Authenticate', 'bearer')


def is_not_found():
    return has_status(404)


def is_ok():
    return has_status(200)


class IsHeaderWithValue(BaseMatcher):
    def __init__(self, header, expected_value):
        self.header = header
        self.expected_value = expected_value

    def _matches(self, response):
        return response.headers.get(self.header, None) == self.expected_value

    def describe_to(self, description):
        description.append_text(
            "contain header %s with value %s" % (self.header, self.expected_value))

    def describe_mismatch(self, actual, description):
        description.append_text("had headers %s" % actual.headers.to_list)


def has_header(name, value):
    return IsHeaderWithValue(name, value)


class IsErrorResponse(BaseMatcher):
    def __init__(self, message):
        self.message = message

    def _matches(self, response):
        try:
            data = json.loads(response.data)
            if data.get('status') != 'error' and response.status_code != 400:
                return False
            # it should not fail with out a message
            if not data.get('message') and not data.get('messages'):
                return False
            if self.message and not (
                    data.get('message') == self.message or
                    self.message not in data.get('messages')):
                return False
            return True
        except ValueError:
            return False

    def describe_to(self, description):
        if not self.message:
            description_message = 'error response with any error message'
        else:
            description_message = 'error response with message: "{}"'.format(
                self.message)
        description.append_text(
            description_message
        )


def is_error_response(message=None):
    return IsErrorResponse(message)


def d_tz(year, month, day, hour=0, minute=0, seconds=0, tzinfo=None):
    return datetime.datetime(year, month, day, hour, minute, seconds,
                             tzinfo=tzinfo or pytz.UTC)


def d(year, month, day, hour=0, minute=0, second=0):
    return datetime.datetime(year=year, month=month, day=day,
                             hour=hour, minute=minute, second=second)


def fixture_path(name):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'features', 'fixtures', name))


def mock_mogrify(template, values):
    """
    >>> mock_mogrify("select %(thing)s from %(other_thing)s ...", {'thing': 'value', 'other_thing': 'other_value'})
    "select 'value' from 'other_value' ..."
    """

    tokens = re.split("(%\([^\)]+\)s)", template)

    return re.sub(
        "\s+",
        " ",
        "".join([_mogrify_token(token, values) for token in tokens])
    ).strip()


def _mogrify_token(token, values):
    match = re.match("%\(([^\(]+)\)s", token)
    if match:
        (key,) = match.groups()
        return "'%s'" % values[key]
    else:
        return token


@contextmanager
def json_fixture(name, parse_dates=False):
    if not parse_dates:
        with open(filename, 'r') as f:
            yield json.loads(f.read())

    def _date_hook(json_dict):
        for (key, value) in json_dict.items():
            try:
                json_dict[key] = parser.parse(value)
            except:
                pass
        return json_dict

    filename = pjoin(dirname(__file__), '..', 'fixtures', name)
    with open(filename, 'r') as f:
        yield json.loads(f.read(), object_hook=_date_hook)


class match(object):
    """Wraps a hamcrest matcher with __eq__

    This allows it to be easily used with mock's assert_called_with family
    of methods.

    See: https://code.google.com/p/mock/issues/detail?id=86#c4
    """
    def __init__(self, matcher):
        self.matcher = matcher

    def __eq__(self, other):
        return self.matcher.matches(other)

import unittest
from datetime import datetime
from hamcrest import *

import pytz

from backdrop.write import api
from backdrop.core.validators import value_is_valid_id, \
    value_is_valid, key_is_valid, value_is_valid_datetime_string


class ValidKeysTestCase(unittest.TestCase):
    def test_some_keys_are_reserved_namespace(self):
        assert_that(key_is_valid("_timestamp"), is_(True))
        assert_that(key_is_valid("_id"), is_(True))
        assert_that(key_is_valid("_name"), is_(False))

    def test_keys_can_be_case_insensitive(self):
        assert_that(key_is_valid("name"), is_(True))
        assert_that(key_is_valid("NAME"), is_(True))

    def test_keys_can_contain_numbers_and_restricted_punctuation(self):
        assert_that(key_is_valid("name54"), is_(True))
        assert_that(key_is_valid("name_of_thing"), is_(True))
        assert_that(key_is_valid("name-of-thing"), is_(True))
        assert_that(key_is_valid("son.of.thing"), is_(True))
        assert_that(key_is_valid("son;of;thing"), is_(False))
        assert_that(key_is_valid("son:of:thing"), is_(False))

    def test_key_cannot_be_empty(self):
        assert_that(key_is_valid(""), is_(False))
        assert_that(key_is_valid("    "), is_(False))
        assert_that(key_is_valid("\t"), is_(False))


class ValidValuesTestCase(unittest.TestCase):
    def test_values_can_be_integers(self):
        assert_that(value_is_valid(1257), is_(True))

    def test_string_values_can_strings(self):
        assert_that(value_is_valid(u"1257"), is_(True))
        assert_that(value_is_valid("1257"), is_(True))

    def test_values_can_be_boolean(self):
        assert_that(value_is_valid(True), is_(True))
        assert_that(value_is_valid(False), is_(True))

    def test_values_cannot_be_arrays(self):
        assert_that(value_is_valid([1, 2, 3, 4]), is_(False))

    def test_values_cannot_be_dictionaries(self):
        assert_that(value_is_valid({'thing': 'I am a thing'}), is_(False))


class TimestampValueIsInDateTimeFormat(unittest.TestCase):
    def test_value_is_of_valid_format(self):
        # our time format = YYYY-MM-DDTHH:MM:SS+HH:MM
        assert_that(
            value_is_valid_datetime_string('2014-01-01T00:00:00+00:00'),
            is_(True))
        assert_that(
            value_is_valid_datetime_string('2014-01-01T00:00:00-00:00'),
            is_(True))

        assert_that(value_is_valid_datetime_string('i am not a time'),
                    is_(False))
        assert_that(
            value_is_valid_datetime_string('abcd-aa-aaTaa:aa:aa+aa:aa'),
            is_(False))
        assert_that(value_is_valid_datetime_string('14-11-01T11:55:11+00:15'),
                    is_(False))
        assert_that(
            value_is_valid_datetime_string('2014-JAN-01T11:55:11+00:15'),
            is_(False))
        assert_that(value_is_valid_datetime_string('2014-1-1T11:55:11+00:15'),
                    is_(False))
        assert_that(value_is_valid_datetime_string('2014-1-1T11:55:11'),
                    is_(False))
        assert_that(
            value_is_valid_datetime_string('2014-aa-aaTaa:aa:55+aa:aa'),
            is_(False))
        assert_that(
            value_is_valid_datetime_string('2012-12-12T00:00:00Z'),
            is_(True)
        )
        assert_that(
            value_is_valid_datetime_string('2012-12-12T00:00:00+0000'),
            is_(True)
        )


class IdValueIsValidTestCase(unittest.TestCase):
    def test_id_value_cannot_be_empty(self):
        assert_that(value_is_valid_id(''), is_(False))
        assert_that(value_is_valid_id('a'), is_(True))

    def test_id_value_cannot_contain_white_spaces(self):
        assert_that(value_is_valid_id('a b'), is_(False))
        assert_that(value_is_valid_id('a    b'), is_(False))
        assert_that(value_is_valid_id('a\tb'), is_(False))

    def test_id_should_be_a_utf8_string(self):
        assert_that(value_is_valid_id(7), is_(False))
        assert_that(value_is_valid_id(None), is_(False))
        assert_that(value_is_valid_id(u'7'), is_(True))


class ValidDateObjectTestCase(unittest.TestCase):
    def test_validation_happens_until_error_or_finish(self):
        #see value validation tests, we don't accept arrays
        my_second_value_is_bad = {
            u'aardvark': u'puppies',
            u'Cthulu': ["R'lyeh"]
        }

        assert_that(
            api.validate_data_object(my_second_value_is_bad).is_valid,
            is_(False))

    def test_validation_for_bad_time_strings(self):
        some_bad_data = {u'_timestamp': u'hammer time'}
        assert_that(
            api.validate_data_object(some_bad_data).is_valid,
            is_(False))
        some_good_data = {u'_timestamp': u'2014-01-01T00:00:00+00:00'}
        assert_that(
            api.validate_data_object(some_good_data).is_valid,
            is_(True))


class DateStringToUTCDateTimeTestCase(unittest.TestCase):
    def test_that_date_strings_get_converted_to_datetimes(self):
        some_datetime = api.time_string_to_utc_datetime(
            '2014-01-02T03:04:05+00:00'
        )

        assert_that(isinstance(some_datetime, datetime), is_(True))
        assert_that(some_datetime,
                    is_(datetime(2014, 1, 2, 3, 4, 5, tzinfo=pytz.utc)))

    def test_that_date_strings_get_converted_to_utc(self):
        some_datetime = api.time_string_to_utc_datetime(
            '2014-01-02T06:04:05+03:30'
        )

        assert_that(isinstance(some_datetime, datetime), is_(True))
        assert_that(some_datetime,
                    is_(datetime(2014, 1, 2, 2, 34, 5, tzinfo=pytz.utc)))

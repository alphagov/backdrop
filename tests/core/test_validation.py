import unittest

from hamcrest import *

from backdrop.core.validation import value_is_valid_id,\
    value_is_valid, key_is_valid, value_is_valid_datetime_string, key_is_reserved


class ValidKeysTestCase(unittest.TestCase):
    def test_keys_can_be_case_insensitive(self):
        assert_that(key_is_valid("name"), is_(True))
        assert_that(key_is_valid("NAME"), is_(True))

    def test_keys_can_contain_numbers_and_restricted_punctuation(self):
        assert_that(key_is_valid("name54"), is_(True))
        assert_that(key_is_valid("name_of_thing"), is_(True))
        assert_that(key_is_valid("son.of.thing"), is_(True))
        assert_that(key_is_valid("name-of-thing"), is_(False))
        assert_that(key_is_valid("son;of;thing"), is_(False))
        assert_that(key_is_valid("son:of:thing"), is_(False))

    def test_keys_must_start_with_letter_or_underscore(self):
        assert_that(key_is_valid("field"), is_(True))
        assert_that(key_is_valid("_field"), is_(True))
        assert_that(key_is_valid("field1"), is_(True))
        assert_that(key_is_valid("Field1"), is_(True))
        assert_that(key_is_valid("1field"), is_(False))

    def test_key_cannot_be_empty(self):
        assert_that(key_is_valid(""), is_(False))
        assert_that(key_is_valid("    "), is_(False))
        assert_that(key_is_valid("\t"), is_(False))


class ReservedKeysTestCase(unittest.TestCase):
    def test_reserved_keys_are_reserved(self):
        assert_that(key_is_reserved("_timestamp"), is_(True))
        assert_that(key_is_reserved("_id"), is_(True))
        assert_that(key_is_reserved("_name"), is_(False))
        assert_that(key_is_reserved("name"), is_(False))


class ValidValuesTestCase(unittest.TestCase):
    def test_values_can_be_integers(self):
        assert_that(value_is_valid(1257), is_(True))

    def test_values_can_be_floats(self):
        assert_that(value_is_valid(123.321), is_(True))

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

        assert_that(
            value_is_valid_datetime_string('i am not a time'),
            is_(False))
        assert_that(
            value_is_valid_datetime_string('abcd-aa-aaTaa:aa:aa+aa:aa'),
            is_(False))
        assert_that(
            value_is_valid_datetime_string('14-11-01T11:55:11+00:15'),
            is_(False))
        assert_that(
            value_is_valid_datetime_string('2014-JAN-01T11:55:11+00:15'),
            is_(False))
        assert_that(
            value_is_valid_datetime_string('2014-1-1T11:55:11+00:15'),
            is_(False))
        assert_that(
            value_is_valid_datetime_string('2014-1-1T11:55:11'),
            is_(False))
        assert_that(
            value_is_valid_datetime_string('2014-aa-aaTaa:aa:55+aa:aa'),
            is_(False))
        assert_that(
            value_is_valid_datetime_string('2012-12-12T00:00:00Z'),
            is_(True))
        assert_that(
            value_is_valid_datetime_string('2012-12-12T00:00:00+0000'),
            is_(True))


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

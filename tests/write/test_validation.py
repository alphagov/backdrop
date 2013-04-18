import unittest

from hamcrest import *

from backdrop.write.validation import validate_data_object
from tests.support.validity_matcher import is_invalid_with_message


class TestValidateDataObject(unittest.TestCase):
    def test_objects_with_invalid_keys_are_disallowed(self):
        validation_result = validate_data_object({
            'foo-bar': 'bar'
        })
        assert_that(validation_result,
                    is_invalid_with_message("foo-bar is not a valid key"))

    def test_objects_with_invalid_values_are_disallowed(self):
        validation_result = validate_data_object({
            'foo': tuple()
        })
        assert_that(validation_result,
                    is_invalid_with_message("() is not a valid value"))

    def test_objects_with_invalid_timestamps_are_disallowed(self):
        validation_result = validate_data_object({
            '_timestamp': 'this is not a timestamp'
        })
        assert_that(validation_result,
                    is_invalid_with_message(
                        "this is not a timestamp is not a valid timestamp"))

    def test_objects_with_invalid_ids_are_disallowed(self):
        validation_result = validate_data_object({
            '_id': 'invalid id'
        })
        assert_that(validation_result,
                    is_invalid_with_message(
                        "invalid id is not a valid _id"))

    def test_objects_with_unrecognised_internal_keys_are_disallowed(self):
        validation_result = validate_data_object({
            '_unknown': 'whatever'
        })
        assert_that(validation_result,
                    is_invalid_with_message(
                        "Unrecognised internal key provided"))


class ValidDateObjectTestCase(unittest.TestCase):
    def test_validation_happens_until_error_or_finish(self):
        #see value validation tests, we don't accept arrays
        my_second_value_is_bad = {
            u'aardvark': u'puppies',
            u'Cthulu': ["R'lyeh"]
        }

        assert_that(
            validate_data_object(my_second_value_is_bad).is_valid,
            is_(False))

    def test_validation_for_bad_time_strings(self):
        some_bad_data = {u'_timestamp': u'hammer time'}
        assert_that(
            validate_data_object(some_bad_data).is_valid,
            is_(False))
        some_good_data = {u'_timestamp': u'2014-01-01T00:00:00+00:00'}
        assert_that(
            validate_data_object(some_good_data).is_valid,
            is_(True))

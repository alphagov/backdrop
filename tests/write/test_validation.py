import unittest

from hamcrest import *

from backdrop.write.validation import validate_data_object


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

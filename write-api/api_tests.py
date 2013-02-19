import unittest
from datetime import datetime
import pytz

from api import key_is_valid, value_is_valid, value_is_valid_datetime_string
import api


class ValidKeysTestCase(unittest.TestCase):
    def test_some_keys_are_reserved_namespace(self):
        self.assertTrue( key_is_valid("_timestamp") )
        self.assertFalse( key_is_valid("_name") )

    def test_keys_can_be_case_insensitive(self):
        self.assertTrue( key_is_valid("name") )
        self.assertTrue( key_is_valid("NAME") )

    def test_keys_can_contain_numbers_and_restricted_punctuation(self):
        self.assertTrue( key_is_valid("name54") )
        self.assertTrue( key_is_valid("name_of_thing") )
        self.assertTrue( key_is_valid("name-of-thing") )
        self.assertTrue( key_is_valid("son.of.thing") )
        self.assertFalse( key_is_valid("son;of;thing") )
        self.assertFalse( key_is_valid("son:of:thing") )


class ValidValuesTestCase(unittest.TestCase):
    def test_values_can_be_integers(self):
        self.assertTrue( value_is_valid(1257) )

    def test_string_values_can_only_be_unicode_strings(self):
        self.assertTrue( value_is_valid( u"1257" ) )
        self.assertFalse( value_is_valid( "1257" ) )

    def test_values_cannot_be_arrays(self):
        self.assertFalse( value_is_valid([1, 2, 3, 4]) )

    def test_values_cannot_be_dictionaries(self):
        self.assertFalse( value_is_valid( {'thing': 'I am a thing'} ) )


class PostDataTestCase(unittest.TestCase):
    def stub_storage(self, bucket_name, data_to_store):
        self.stored_bucket = bucket_name
        self.stored_data = data_to_store

    def setUp(self):
        self.app = api.app.test_client()
        self.stored_bucket = None
        self.stored_data = None

    def test_data_gets_stored(self):
        api.store_objects = self.stub_storage

        self.app.post(
            '/foo-bucket/',
            data = '{"foo": "bar"}',
            content_type = "application/json"
        )

        self.assertTrue( self.stored_bucket == 'foo-bucket' )
        self.assertTrue( self.stored_data[0]['foo'] == 'bar' )

    def test_bucket_name_validation(self):
        response = self.app.post(
            '/_foo-bucket/',
            data = '{"foo": "bar"}',
            content_type = "application/json"
        )

        self.assertEqual( response.status_code, 400 )

    def test__timestamps_get_stored_as_utc_datetimes(self):
        api.store_objects = self.stub_storage
        expected_time = {
            u'_timestamp':
            datetime(2014, 1, 2, 3, 49, 0, tzinfo=pytz.utc)
        }

        self.app.post(
            '/bucket/',
            data = '{"_timestamp": "2014-01-02T03:49:00+00:00"}',
            content_type = "application/json"
        )

        self.assertEqual( self.stored_bucket, 'bucket' )
        self.assertEqual( self.stored_data, [expected_time] )


class TimestampValueIsInDateTimeFormat(unittest.TestCase):
    def test_value_is_of_valid_format(self):
        # our time format = YYYY-MM-DDTHH:MM:SS+HH:MM
        self.assertTrue(
            value_is_valid_datetime_string('2014-01-01T00:00:00+00:00')
        )
        self.assertTrue(
            value_is_valid_datetime_string('2014-01-01T00:00:00-00:00')
        )

        self.assertFalse(
            value_is_valid_datetime_string('i am not a time')
        )
        self.assertFalse(
            value_is_valid_datetime_string('abcd-aa-aaTaa:aa:aa+aa:aa')
        )
        self.assertFalse(
            value_is_valid_datetime_string('14-11-01T11:55:11+00:15')
        )
        self.assertFalse(
            value_is_valid_datetime_string('2014-JAN-01T11:55:11+00:15')
        )
        self.assertFalse(
            value_is_valid_datetime_string('2014-1-1T11:55:11+00:15')
        )
        self.assertFalse(
            value_is_valid_datetime_string('2014-1-1T11:55:11')
        )
        self.assertFalse(
            value_is_valid_datetime_string('2014-aa-aaTaa:aa:55+aa:aa')
        )


class ValidDateObjectTestCase(unittest.TestCase):
    def test_validation_happens_until_error_or_finish(self):
        #see value validation tests, we don't accept arrays
        my_second_value_is_bad = {
            u'aardvark': u'puppies',
            u'Cthulu': ["R'lyeh"]
        }

        self.assertTrue( api.invalid_data_object(my_second_value_is_bad) )

    def test_validation_for_bad_time_strings(self):
        some_bad_data = {u'_timestamp': u'hammer time'}
        self.assertTrue( api.invalid_data_object(some_bad_data) )
        some_good_data = {u'_timestamp': u'2014-01-01T00:00:00+00:00'}
        self.assertFalse( api.invalid_data_object(some_good_data) )


class DateStringToUTCDateTimeTestCase(unittest.TestCase):
    def test_that_date_strings_get_converted_to_datetimes(self):
        some_datetime = api.time_string_to_utc_datetime(
            '2014-01-02T03:04:05+00:00'
        )

        self.assertTrue( isinstance(some_datetime, datetime) )
        self.assertEquals(
            some_datetime,
            datetime(2014, 1, 2, 3, 4, 5, tzinfo=pytz.utc)
        )

    def test_that_date_strings_get_converted_to_utc(self):
        some_datetime = api.time_string_to_utc_datetime(
            '2014-01-02T06:04:05+03:30'
        )

        self.assertTrue( isinstance(some_datetime, datetime) )
        self.assertEquals(
            some_datetime,
            datetime(2014, 1, 2, 2, 34, 5, tzinfo=pytz.utc)
        )

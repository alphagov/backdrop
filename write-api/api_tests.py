from api import key_is_valid, value_is_valid

import api
import unittest


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
    def stub_storage(self, bucket_name):
        self.stored_bucket = bucket_name
    
    def setUp(self):
        self.app = api.app.test_client()
        self.stored_bucket = None
    
    def test_data_gets_stored(self):
        api.store_valid_objects = self.stub_storage
        self.app.post(
            '/foo-bucket/',
            data = '{"foo": "bar"}',
            content_type = "application/json"
        )
        self.assertTrue(self.stored_bucket == 'foo-bucket')

    def test_bucket_name_validation(self):
        response = self.app.post(
            '/_foo-bucket/',
            data = '{"foo": "bar"}',
            content_type = "application/json"
        )
        self.assertEqual(response.status_code, 400)

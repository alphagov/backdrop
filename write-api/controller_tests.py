from datetime import datetime
import json
import unittest
import pytz
import api

__author__ = 'grogers'


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
            '/foo-bucket',
            data = '{"foo": "bar"}',
            content_type = "application/json"
        )

        self.assertTrue( self.stored_bucket == 'foo-bucket' )
        self.assertTrue( self.stored_data[0]['foo'] == 'bar' )

    def test_bucket_name_validation(self):
        response = self.app.post(
            '/_foo-bucket',
            data = '{"foo": "bar"}',
            content_type = "application/json"
        )

        self.assertEqual( response.status_code, 400 )

    def test__timestamps_get_stored_as_utc_datetimes(self):
        api.store_objects = self.stub_storage
        expected_time = {
            u'_timestamp': datetime(2014, 1, 2, 3, 49, 0, tzinfo=pytz.utc)
        }

        self.app.post(
            '/bucket',
            data = '{"_timestamp": "2014-01-02T03:49:00+00:00"}',
            content_type = "application/json"
        )

        self.assertEqual( self.stored_bucket, 'bucket' )
        self.assertEqual( self.stored_data, [expected_time] )

    def test_data_gets_stored(self):
        response = self.app.post(
            '/foo-bucket',
            data = '{"": ""}',
            content_type = "application/json"
        )

        self.assertEqual(response.status_code, 400)


class ApiHealthCheckTestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()
        self.stored_bucket = None
        self.stored_data = None

    def test_api_exposes_a_healthcheck(self):
        response = self.app.get("/_status")

        self.assertEquals(200, response.status_code)
        self.assertEquals("application/json", response.headers["Content-Type"])

        entity = json.loads(response.data)
        self.assertEquals("ok", entity["status"])

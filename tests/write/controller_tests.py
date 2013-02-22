import test_helper

from datetime import datetime
import json
import unittest
from hamcrest import *
import pytz
from test_helpers import is_bad_request, is_ok

from performance_platform.write import api


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

        assert_that( self.stored_bucket, is_("foo-bucket"))
        assert_that( self.stored_data[0], has_entry("foo", "bar"))

    def test_bucket_name_validation(self):
        response = self.app.post(
            '/_foo-bucket',
            data = '{"foo": "bar"}',
            content_type = "application/json"
        )

        assert_that( response, is_bad_request() )

    def test__timestamps_get_stored_as_utc_datetimes(self):
        api.store_objects = self.stub_storage
        expected_event_with_time = {
            u'_timestamp': datetime(2014, 1, 2, 3, 49, 0, tzinfo=pytz.utc)
        }

        self.app.post(
            '/bucket',
            data = '{"_timestamp": "2014-01-02T03:49:00+00:00"}',
            content_type = "application/json"
        )

        assert_that( self.stored_bucket, is_("bucket"))
        assert_that( self.stored_data, contains(expected_event_with_time) )

    def test_data_with_empty_keys_400s(self):
        response = self.app.post(
            '/foo-bucket',
            data = '{"": ""}',
            content_type = "application/json"
        )

        assert_that( response, is_bad_request())

    def test__id_gets_stored(self):
        api.store_objects = self.stub_storage
        response = self.app.post(
            '/foo',
            data = '{"_id": "foo"}',
            content_type = "application/json"
        )

        assert_that(response, is_ok())
        assert_that(self.stored_data, contains({"_id": u"foo"}))

    def test_invalid__id_returns_400(self):
        response = self.app.post(
            '/foo',
            data = '{"_id": "f o o"}',
            content_type = "application/json"
        )

        assert_that(response, is_bad_request())


class ApiHealthCheckTestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()
        self.stored_bucket = None
        self.stored_data = None

    def test_api_exposes_a_healthcheck(self):
        response = self.app.get("/_status")

        assert_that(response, is_ok())
        assert_that(response.headers["Content-Type"], is_("application/json"))

        entity = json.loads(response.data)
        assert_that(entity["status"], is_("ok"))

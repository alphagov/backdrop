from datetime import datetime
import json
import unittest

from hamcrest import *
import pytz
from mock import patch
from backdrop.core.records import Record

from tests.support.test_helpers import is_bad_request, is_ok, is_error_response
from backdrop.write import api


class PostDataTestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()

    def test_request_must_be_json(self):
        response = self.app.post(
            '/foo',
            data='foobar'
        )

        assert_that( response, is_bad_request())
        assert_that( response, is_error_response())

    @patch("backdrop.write.api.store")
    def test_data_gets_stored(self, store):
        self.app.post(
            '/foo-bucket',
            data = '{"foo": "bar"}',
            content_type = "application/json"
        )

        store.get_bucket.assert_called_with("foo-bucket")
        store.get_bucket.return_value.store.assert_called_with(
            [Record({"foo": "bar"})]
        )

    def test_bucket_name_validation(self):
        response = self.app.post(
            '/_foo-bucket',
            data = '{"foo": "bar"}',
            content_type = "application/json"
        )

        assert_that( response, is_bad_request() )
        assert_that( response, is_error_response())

    @patch("backdrop.write.api.store")
    def test__timestamps_get_stored_as_utc_datetimes(self, store):
        expected_event_with_time = {
            u'_timestamp': datetime(2014, 1, 2, 3, 49, 0, tzinfo=pytz.utc)
        }

        self.app.post(
            '/bucket',
            data = '{"_timestamp": "2014-01-02T03:49:00+00:00"}',
            content_type = "application/json"
        )

        store.get_bucket.assert_called_with("bucket")
        store.get_bucket.return_value.store.assert_called_with(
            [Record(expected_event_with_time)]
        )

    def test_data_with_empty_keys_400s(self):
        response = self.app.post(
            '/foo-bucket',
            data = '{"": ""}',
            content_type = "application/json"
        )

        assert_that( response, is_bad_request())
        assert_that( response, is_error_response())

    @patch("backdrop.write.api.store")
    def test__id_gets_stored(self, store):
        response = self.app.post(
            '/foo',
            data = '{"_id": "foo"}',
            content_type = "application/json"
        )

        assert_that(response, is_ok())
        store.get_bucket.return_value.store.assert_called_with(
            [Record({"_id": "foo"})]
        )

    def test_invalid__id_returns_400(self):
        response = self.app.post(
            '/foo',
            data = '{"_id": "f o o"}',
            content_type = "application/json"
        )

        assert_that( response, is_bad_request())
        assert_that( response, is_error_response())


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

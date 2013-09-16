from datetime import datetime
import json
import unittest

from hamcrest import *
import pytz
from mock import patch
from backdrop.core.records import Record
from tests.support.bucket import stub_bucket

from tests.support.test_helpers import is_bad_request, is_ok, \
    is_error_response, has_status, is_not_found
from tests.support.test_helpers import is_unauthorized
from backdrop.write import api


class PostDataTestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()

    @stub_bucket("foo")
    def test_needs_an_authorization_header_even_if_no_token_is_configured(self):
        response = self.app.post(
            '/foo',
            data='[]',
        )

        assert_that( response, is_unauthorized())
        assert_that( response, is_error_response())

    @stub_bucket("foo", bearer_token="foo-bearer-token")
    def test_needs_an_authorization_header(self):
        response = self.app.post(
            '/foo',
            data='[]',
        )

        assert_that( response, is_unauthorized())
        assert_that( response, is_error_response())

    @stub_bucket("foo", bearer_token="foo-bearer-token")
    def test_authorization_header_must_be_correct_format(self):
        response = self.app.post(
            '/foo',
            data='[]',
            headers=[('Authorization', 'Bearer')],
        )

        assert_that( response, is_unauthorized())
        assert_that( response, is_error_response())

    @stub_bucket("foo", bearer_token="foo-bearer-token")
    def test_authorization_header_must_match_server_side_value(self):
        response = self.app.post(
            '/foo',
            data='[]',
            headers=[('Authorization', 'Bearer not-foo-bearer-token')],
        )

        assert_that( response, is_unauthorized())
        assert_that( response, is_error_response())

    @stub_bucket("foo", bearer_token="foo-bearer-token")
    def test_request_must_be_json(self):
        response = self.app.post(
            '/foo',
            data='foobar',
            headers=[('Authorization', 'Bearer foo-bearer-token')],
        )

        assert_that( response, is_bad_request())
        assert_that( response, is_error_response())

    @stub_bucket("foo_bucket", bearer_token="foo_bucket-bearer-token")
    @patch("backdrop.core.bucket.Bucket.store")
    def test_empty_list_gets_accepted(self, store):
        self.app.post(
            '/foo_bucket',
            data='[]',
            content_type="application/json",
            headers=[('Authorization', 'Bearer foo_bucket-bearer-token')],
        )

        store.assert_called_with(
            []
        )

    @stub_bucket("foo_bucket", bearer_token="foo_bucket-bearer-token")
    @patch("backdrop.core.bucket.Bucket.store")
    def test_data_gets_stored(self, store):
        self.app.post(
            '/foo_bucket',
            data = '{"foo": "bar"}',
            content_type = "application/json",
            headers=[('Authorization', 'Bearer foo_bucket-bearer-token')],
        )

        store.assert_called_with(
            [Record({"foo": "bar"})]
        )

    @stub_bucket("foo", bearer_token="foo-bearer-token")
    @patch("backdrop.core.bucket.Bucket.store")
    def test__timestamps_get_stored_as_utc_datetimes(self, store):
        expected_event_with_time = {
            u'_timestamp': datetime(2014, 1, 2, 3, 49, 0, tzinfo=pytz.utc)
        }

        self.app.post(
            '/foo',
            data = '{"_timestamp": "2014-01-02T03:49:00+00:00"}',
            content_type = "application/json",
            headers=[('Authorization', 'Bearer foo-bearer-token')],
        )

        store.assert_called_with(
            [Record(expected_event_with_time)]
        )

    @stub_bucket("foo_bucket", bearer_token="foo_bucket-bearer-token")
    def test_data_with_empty_keys_400s(self):
        response = self.app.post(
            '/foo_bucket',
            data = '{"": ""}',
            content_type = "application/json",
            headers=[('Authorization', 'Bearer foo_bucket-bearer-token')],
        )

        assert_that( response, is_bad_request())
        assert_that( response, is_error_response())

    @stub_bucket("foo", bearer_token="foo-bearer-token")
    @patch("backdrop.core.bucket.Bucket.store")
    def test__id_gets_stored(self, store):
        response = self.app.post(
            '/foo',
            data = '{"_id": "foo"}',
            content_type = "application/json",
            headers=[('Authorization', 'Bearer foo-bearer-token')],
        )

        assert_that(response, is_ok())
        store.assert_called_with(
            [Record({"_id": "foo"})]
        )

    @stub_bucket("foo", bearer_token="foo-bearer-token")
    def test_invalid__id_returns_400(self):
        response = self.app.post(
            '/foo',
            data = '{"_id": "f o o"}',
            content_type = "application/json",
            headers=[('Authorization', 'Bearer foo-bearer-token')],
        )

        assert_that( response, is_bad_request())
        assert_that( response, is_error_response())

    @patch("backdrop.write.api.statsd")
    @patch("backdrop.core.bucket.Bucket.parse_and_store")
    def test_exception_handling(self, parse_and_store, statsd):
        parse_and_store.side_effect = RuntimeError("BOOM")

        response = self.app.post(
            "/foo",
            data="{}",
            content_type='application/json',
            headers=[('Authorization', 'Bearer foo-bearer-token')]
        )

        assert_that(response, has_status(500))
        assert_that(response, is_error_response())

        statsd.incr.assert_called_with("write.error", bucket="foo")


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

    @patch("backdrop.write.api.statsd")
    @patch("backdrop.write.api.db")
    def test_exception_handling(self, db, statsd):
        db.alive.side_effect = ValueError("BOOM")

        response = self.app.get("/_status")

        assert_that(response, has_status(500))
        assert_that(response, is_error_response())

        statsd.incr.assert_called_with("write.error", bucket="/_status")


class UploadPageTestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()

    def test_invalid_bucket_name_returns_400(self):
        response = self.app.get("/$invalid_bucket/upload")
        assert_that(response, is_not_found())

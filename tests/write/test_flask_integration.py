import json
import unittest

from hamcrest import assert_that, is_
from mock import patch
from tests.support.performanceplatform_client import fake_data_set_exists

from tests.support.test_helpers import is_bad_request, is_ok, \
    is_error_response, has_status, is_not_found
from tests.support.test_helpers import is_unauthorized
from backdrop.write import api


class PostDataTestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()

    @fake_data_set_exists("foo")
    def test_needs_an_authorization_header_even_if_no_token_is_configured(self):
        response = self.app.post(
            '/foo',
            data='[]',
        )

        assert_that( response, is_unauthorized())
        assert_that( response, is_error_response())

    @fake_data_set_exists("foo", bearer_token="foo-bearer-token")
    def test_needs_an_authorization_header(self):
        response = self.app.post(
            '/foo',
            data='[]',
        )

        assert_that( response, is_unauthorized())
        assert_that( response, is_error_response())

    @fake_data_set_exists("foo", bearer_token="foo-bearer-token")
    def test_authorization_header_must_be_correct_format(self):
        response = self.app.post(
            '/foo',
            data='[]',
            headers=[('Authorization', 'Bearer')],
        )

        assert_that( response, is_unauthorized())
        assert_that( response, is_error_response())

    @fake_data_set_exists("foo", bearer_token="foo-bearer-token")
    def test_authorization_header_must_match_server_side_value(self):
        response = self.app.post(
            '/foo',
            data='[]',
            headers=[('Authorization', 'Bearer not-foo-bearer-token')],
        )

        assert_that( response, is_unauthorized())
        assert_that( response, is_error_response())

    @fake_data_set_exists("foo", bearer_token="foo-bearer-token")
    def test_request_must_be_json(self):
        response = self.app.post(
            '/foo',
            data='foobar',
            headers=[('Authorization', 'Bearer foo-bearer-token')],
        )

        assert_that( response, is_bad_request())
        assert_that( response, is_error_response("ValidationError('Expected header: Content-type: application/json',)"))

    @fake_data_set_exists("foo_data_set", bearer_token="foo_data_set-bearer-token")
    @patch("backdrop.core.data_set.DataSet.store")
    def test_empty_list_gets_accepted(self, store):
        self.app.post(
            '/foo_data_set',
            data='[]',
            content_type="application/json",
            headers=[('Authorization', 'Bearer foo_data_set-bearer-token')],
        )

        store.assert_called_with(
            []
        )

    @fake_data_set_exists("foo_data_set", bearer_token="foo_data_set-bearer-token")
    @patch("backdrop.core.data_set.DataSet.store")
    def test_data_gets_stored(self, store):
        self.app.post(
            '/foo_data_set',
            data='{"foo": "bar"}',
            content_type="application/json",
            headers=[('Authorization', 'Bearer foo_data_set-bearer-token')],
        )

        store.assert_called_with(
            [{"foo": "bar"}]
        )

    @fake_data_set_exists("foo_data_set", bearer_token="foo_data_set-bearer-token")
    @patch("backdrop.core.data_set.DataSet.create_if_not_exists")
    @patch("backdrop.core.data_set.DataSet.store")
    def test_data_set_is_created_on_write(self, store, create_if_not_exists):
        self.app.post(
            '/foo_data_set',
            data='{"foo": "bar"}',
            content_type="application/json",
            headers=[("Authorization", "Bearer foo_data_set-bearer-token")],
        )

        create_if_not_exists.assert_called_once_with()

    @fake_data_set_exists("foo_data_set", bearer_token="foo_data_set-bearer-token")
    def test_data_with_empty_keys_400s(self):
        response = self.app.post(
            '/foo_data_set',
            data = '{"": ""}',
            content_type = "application/json",
            headers=[('Authorization', 'Bearer foo_data_set-bearer-token')],
        )

        assert_that( response, is_bad_request())
        assert_that( response, is_error_response())

    @fake_data_set_exists("foo", bearer_token="foo-bearer-token")
    @patch("backdrop.core.data_set.DataSet.store")
    def test__id_gets_stored(self, store):
        response = self.app.post(
            '/foo',
            data = '{"_id": "foo"}',
            content_type = "application/json",
            headers=[('Authorization', 'Bearer foo-bearer-token')],
        )

        assert_that(response, is_ok())
        store.assert_called_with(
            [{"_id": "foo"}]
        )

    @fake_data_set_exists("foo", bearer_token="foo-bearer-token")
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
    @patch("backdrop.core.data_set.DataSet.store")
    @fake_data_set_exists("foo", bearer_token="foo-bearer-token")
    def test_exception_handling(self, store, statsd):
        store.side_effect = RuntimeError("BOOM")

        response = self.app.post(
            "/foo",
            data="{}",
            content_type='application/json',
            headers=[('Authorization', 'Bearer foo-bearer-token')]
        )

        assert_that(response, has_status(500))
        assert_that(response, is_error_response())

        statsd.incr.assert_called_with("write.error", data_set="foo")


class ApiHealthCheckTestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()
        self.stored_data_set = None
        self.stored_data = None

    def test_api_exposes_a_healthcheck(self):
        response = self.app.get("/_status")

        assert_that(response, is_ok())
        assert_that(response.headers["Content-Type"], is_("application/json"))

        entity = json.loads(response.data)
        assert_that(entity["status"], is_("ok"))

    @patch("backdrop.write.api.statsd")
    @patch("backdrop.write.api.storage")
    def test_exception_handling(self, storage, statsd):
        storage.alive.side_effect = ValueError("BOOM")

        response = self.app.get("/_status")

        assert_that(response, has_status(500))
        assert_that(response, is_error_response())

        statsd.incr.assert_called_with("write.error", data_set="/_status")


class UploadPageTestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()

    def test_invalid_data_set_name_returns_400(self):
        response = self.app.get("/$invalid_data_set/upload")
        assert_that(response, is_not_found())

import unittest
from flask import session, request
from hamcrest import *
from mock import patch
from werkzeug.urls import url_decode
from backdrop.write import api
from tests.support.test_helpers import has_status


class TestSignonIntegration(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()
        self.app = api.app

    def test_signing_in_redirects_me_to_signon(self):
        response = self.client.get('/sign_in')

        params = url_decode(response.headers['Location'].split('?')[1])

        assert_that(response, has_status(302))
        assert_that(params, has_entry('response_type', 'code'))
        assert_that(params, has_entry('redirect_uri',
                                      'http://localhost/authorized'))
        assert_that(params, has_entry('client_id',
                                      api.app.config['CLIENT_ID']))

    @patch("backdrop.write.api.app.oauth_service")
    def test_authorized_handler_redirects_you_to_index_page(
            self, oauth_service):
        user_is_authorized_to_see_backdrop = True

        code = "we don't care at all"
        oauth_service.exchange.return_value = "we don't care at all"
        oauth_service.user_details.return_value = {
            "user": {"name": "we don't care at all"}
        }, user_is_authorized_to_see_backdrop

        response = self.client.get('/authorized?code=%s' % code)

        path = response.headers['Location'].split('?')[0]
        assert_that(response, has_status(302))
        assert_that(path, is_('http://localhost/'))

    @patch("backdrop.write.api.app.oauth_service")
    def test_user_is_stored_in_session_when_authorized(self, oauth_service):
        oauth_service.exchange.return_value = "don't care"
        oauth_service.user_details.return_value = \
            {"user": {"name": "test"}}, True

        with self.app.test_request_context('/authorized?code=12345'):
            self.app.dispatch_request()
            assert_that(session.get('user'), is_('test'))

    @patch("backdrop.write.api.app.oauth_service")
    def test_user_is_logged_out_when_visiting_sign_out(self, oauth_service):
        oauth_service.exchange.return_value = "don't care"
        oauth_service.user_details.return_value = \
            {"user": {"name": "test"}}, True
        with self.app.test_request_context('/authorized?code=12345'):
            self.app.dispatch_request()
            assert_that(session.get('user'), is_("test"))

        with self.app.test_request_context('/sign_out'):
            self.app.dispatch_request()
            assert_that(session.get('user'), is_(None))

import unittest
from flask import session, request
from hamcrest import *
from mock import patch
from werkzeug.urls import url_decode
from backdrop.write import api
from backdrop.write.permissions import Permissions
from tests.support.test_helpers import has_status


class TestSignonIntegration(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()
        self.app = api.app

    def test_signing_in_redirects_me_to_signon(self):
        response = self.client.get('/_user/sign_in')

        params = url_decode(response.headers['Location'].split('?')[1])

        assert_that(response, has_status(302))
        assert_that(params, has_entry('response_type', 'code'))
        assert_that(params, has_entry('redirect_uri',
                                      'http://localhost/_user/authorized'))
        assert_that(params, has_entry('client_id',
                                      api.app.config['CLIENT_ID']))

    def stub_oauth(self,
                   oauth_service,
                   user_name="we don't care at all",
                   user_email="we don't care at all",
                   authorized=True):
        oauth_service.exchange.return_value = "we don't care at all"
        oauth_service.user_details.return_value = {
            "user": {
                "name": user_name,
                "email": user_email
            }
        }, authorized

    @patch("backdrop.write.api.app.oauth_service")
    def test_authorized_handler_redirects_you_to_index_page(
            self, oauth_service):

        self.stub_oauth(oauth_service, authorized=True)

        response = self.client.get('/_user/authorized?code=any_code')

        path = response.headers['Location'].split('?')[0]
        assert_that(response, has_status(302))
        assert_that(path, is_('http://localhost/'))

    @patch("backdrop.write.api.app.oauth_service")
    def test_user_is_stored_in_session_when_authorized(self, oauth_service):
        self.stub_oauth(oauth_service, user_name="test", user_email="test@example.com", authorized=True)

        with self.app.test_request_context('/_user/authorized?code=12345'):
            self.app.dispatch_request()
            assert_that(session.get('user'), is_({"name": "test", "email": "test@example.com"}))

    @patch("backdrop.write.api.app.oauth_service")
    def test_user_is_logged_out_when_visiting_sign_out(self, oauth_service):
        self.stub_oauth(oauth_service, user_name="test", user_email="test@example.com", authorized=True)

        with self.app.test_request_context('/_user/authorized?code=12345'):
            self.app.dispatch_request()
            assert_that(session.get('user'), is_({"name": "test", "email": "test@example.com"}))

        with self.app.test_request_context('/_user/sign_out'):
            self.app.dispatch_request()
            assert_that(session.get('user'), is_(None))

    @patch("backdrop.write.api.app.oauth_service")
    def test_user_is_redirected_to_not_authorized_page_for_bad_permissions(
            self, oauth_service):
        self.stub_oauth(oauth_service, user_name="test", user_email="test@example.com", authorized=False)

        with self.app.test_request_context('/_user/authorized?code=12345'):
            response = self.app.dispatch_request()
            path = response.headers['Location'].split('?')[0]
            assert_that(session.get('user'), is_(None))
            assert_that(path, is_('/_user/not_authorized'))
            assert_that(response, has_status(302))

    def test_user_top_level_redirects_to_index_for_now(self):
        response = self.client.get('/_user')
        assert_that(response, has_status(302))

    def test_returning_a_400_when_auth_code_is_not_present(self):
        response = self.client.get('/_user/authorized')
        assert_that(response, has_status(400))

    def test_upload_page_redirects_non_authenticated_user_to_sign_in(self):
        self.given_user_is_not_signed_in()

        response = self.client.get('/test/upload')
        assert_that(response, has_status(302))

    def test_upload_page_is_not_found_if_user_has_no_permissions(self):
        self.given_bucket_permissions("test", [])
        self.given_user_is_signed_in_as(email="bob@example.com")

        response = self.client.get('/test/upload')
        assert_that(response, has_status(404))

    def test_upload_page_is_available_to_user_with_permission(self):
        self.given_bucket_permissions("test", [ "bob@example.com" ])
        self.given_user_is_signed_in_as(email="bob@example.com")

        response = self.client.get('/test/upload')
        assert_that(response, has_status(200))

    # utility methods

    def given_user_is_signed_in_as(self, name="testuser", email="testuser@example.com"):
        with self.client.session_transaction() as session:
            session["user"] = {
                "name": name,
                "email": email
            }

    def given_user_is_not_signed_in(self):
        with self.client.session_transaction() as session:
            if "user" in session:
                del session["user"]

    def given_bucket_permissions(self, bucket, users):
        self.app.permissions = Permissions({
            bucket: users
        })

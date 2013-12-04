import json
import unittest
from hamcrest import *
from mock import patch, Mock
from requests import Response
from backdrop.write import api, signonotron2
from backdrop.write.signonotron2 import Signonotron2
from tests.support.test_helpers import has_status


class Signonotron2TestCase(unittest.TestCase):
    def setUp(self):
        self.ctx = api.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_authorize_returns_a_url_to_signon_service(self):
        oauth_service = Signonotron2(None, None, None, "")
        oauth_service.signon = Mock()
        oauth_service.signon.get_authorize_url.return_value = "http://example.com"

        url = oauth_service.authorize()

        assert_that(url, equal_to("http://example.com"))

    def test_exchange_returns_none_when_code_is_none(self):
        oauth_service = Signonotron2(None, None, None, "")
        oauth_service.signon = Mock()
        response = Response()
        response.status_code = 401
        oauth_service.signon.get_raw_access_token.return_value = response

        assert_that(oauth_service.exchange(None), is_(None))

    def test_exchange_when_code_is_rejected(self):
        oauth_service = Signonotron2(None, None, None, "")
        oauth_service.signon = Mock()
        response = Response()
        response.status_code = 401
        oauth_service.signon.get_raw_access_token.return_value = response

        assert_that(oauth_service.exchange("code to reject"), is_(None))

    @patch("rauth.service.process_token_request")
    def test_exchange_when_code_is_accepted(self, process_token_request):
        oauth_service = Signonotron2(None, None, None, "")
        oauth_service.signon = Mock()
        response = Response()
        response.status_code = 200
        oauth_service.signon.get_raw_access_token.return_value = response
        process_token_request.return_value = tuple(["access toucan"])

        assert_that(
            oauth_service.exchange("code to accept"),
            is_("access toucan"))

    def test_returns_no_user_details_if_access_token_is_none(self):
        oauth_service = Signonotron2(None, None, None, "")

        user_details = oauth_service.user_details(None)

        assert_that(user_details, is_((None, None)))

    def test_user_details_if_access_token_is_rejected(self):
        oauth_service = Signonotron2(None, None, None, "")
        oauth_service.signon = Mock()
        session_object = Mock()
        response = Response()
        response._content = ""
        response.status_code = 401
        session_object.get.return_value = response
        oauth_service.signon.get_session.return_value = session_object

        user_details = oauth_service.user_details("token is rejected")

        assert_that(user_details, is_((None, None)))

    def test_user_details_if_access_token_is_accepted(self):
        oauth_service = Signonotron2(None, None, None, "")
        oauth_service.signon = Mock()
        session_object = Mock()
        response = Response()
        user_details_json = \
            { "user": {"name": "Gareth The Wizard", "permissions": "signin"}}
        response._content = json.dumps(user_details_json)
        response.status_code = 200
        session_object.get.return_value = response
        oauth_service.signon.get_session.return_value = session_object

        user_details = oauth_service.user_details("token is accepted")

        assert_that(user_details, is_((user_details_json, True)))

    def test_returns_none_and_logs_error_if_cannot_parse_token(self):
        mock_logger = Mock()
        signonotron2.log = mock_logger
        oauth_service = Signonotron2(None, None, None, "")
        oauth_service.signon = Mock()
        response = Response()
        response._content = '{"foo":"bar"}'
        response.status_code = 200
        oauth_service.signon.get_raw_access_token.return_value = response

        access_token = oauth_service.exchange("top secret code")
        assert_that(access_token, is_(None))
        assert_that(mock_logger.warn.call_args[0][0],
                    starts_with('Could not parse token from response'))

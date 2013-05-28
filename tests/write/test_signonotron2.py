import json
import unittest
from hamcrest import assert_that, is_
from mock import patch, Mock
from requests import Response
from backdrop.write import api
from backdrop.write.signonotron2 import Signonotron2
from tests.support.test_helpers import has_status


class Signonotron2TestCase(unittest.TestCase):
    def setUp(self):
        self.ctx = api.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_authorize_returns_a_redirect_to_signon_service(self):
        oauth_service = Signonotron2(None, None)
        oauth_service.signon = Mock()
        oauth_service.signon.get_authorize_url.return_value = ""

        response = oauth_service.authorize()

        assert_that(response, has_status(302))

    def test_exchange_returns_none_when_code_is_none(self):
        oauth_service = Signonotron2(None, None)
        oauth_service.signon = Mock()
        response = Response()
        response.status_code = 401
        oauth_service.signon.get_raw_access_token.return_value = response

        assert_that(oauth_service.exchange(None), is_(None))

    def test_exchange_when_code_is_rejected(self):
        oauth_service = Signonotron2(None, None)
        oauth_service.signon = Mock()
        response = Response()
        response.status_code = 401
        oauth_service.signon.get_raw_access_token.return_value = response

        assert_that(oauth_service.exchange("code to reject"), is_(None))

    @patch("rauth.service.process_token_request")
    def test_exchange_when_code_is_accepted(self, process_token_request):
        oauth_service = Signonotron2(None, None)
        oauth_service.signon = Mock()
        response = Response()
        response.status_code = 200
        oauth_service.signon.get_raw_access_token.return_value = response
        process_token_request.return_value = tuple(["access toucan"])

        assert_that(
            oauth_service.exchange("code to accept"),
            is_("access toucan"))

    def test_returns_no_user_details_if_access_token_is_none(self):
        oauth_service = Signonotron2(None, None)

        user_details = oauth_service.user_details(None)

        assert_that(user_details, is_((None, None)))

    def test_user_details_if_access_token_is_rejected(self):
        oauth_service = Signonotron2(None, None)
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
        oauth_service = Signonotron2(None, None)
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

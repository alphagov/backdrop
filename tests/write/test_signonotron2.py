import unittest
from hamcrest import assert_that, is_
from backdrop.write.signonotron2 import Signonotron2


class Signonotron2TestCase(unittest.TestCase):

    def test_returns_no_details_if_access_token_is_none(self):
        oauth_service = Signonotron2(None, None)

        user_details = oauth_service.user_details(None)

        assert_that(user_details, is_((None, None)))

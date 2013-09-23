from tests.support.oauth_test_case import OauthTestCase
from hamcrest import assert_that, has_entry, is_, has_entries
from tests.support.test_helpers import has_status

class TestSSOIntegration(OauthTestCase):

    def test_accepts_posts_to_reauth(self):
        response = self.client.post(
            '/auth/gds/api/users/1234'
        )

        assert_that(response, has_status(200))

    def test_accepts_put_to_update(self):
        response = self.client.put(
            '/auth/gds/api/users/1234/reauth'
        )

        assert_that(response, has_status(200))

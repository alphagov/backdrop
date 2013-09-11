from StringIO import StringIO
from hamcrest import assert_that
from tests.support.oauth_test_case import OauthTestCase
from tests.support.test_helpers import has_status


class TestUploadContentType(OauthTestCase):
    def test_accepts_content_type_for_csv(self):
        self.given_user_is_signed_in_as(name="test", email="test@example.com")
        self.given_bucket_permissions(email="test@example.com",
                                      buckets=['test'])
        response = self.client.post(
            'test/upload',
            data={
                'file': (StringIO('foo, bar'), 'a_big_csv.csv')
            }
        )

        assert_that(response, has_status(200))

    def test_rejects_content_type_for_exe(self):
        self.given_user_is_signed_in_as(name="test", email="test@example.com")
        self.given_bucket_permissions(email="test@example.com",
                                      buckets=['test'])

        response = self.client.post(
            'test/upload',
            data = {
                'file': (StringIO('virus virus virus'), 'kittens.exe')
            }
        )

        assert_that(response, has_status(400))

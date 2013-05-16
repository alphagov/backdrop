from hamcrest import assert_that
from backdrop.write.validation import bearer_token_is_valid


class BearerTokenIsValid(object):
    def test_bearer_token_is_valid(self):
        tokens = {
            "bucket": "token"
        }
        auth_header = "Authorization: token"
        bucket_name = "bucket"

        assert_that(bearer_token_is_valid(tokens, auth_header, bucket_name))

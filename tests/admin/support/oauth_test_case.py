import unittest
from backdrop.admin import app


class OauthTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        # Hit a url to make the oauth_service
        self.client.get('/')
        self.app = app.app

    def given_user_is_signed_in_as(self, name="testuser",
                                   email="testuser@example.com"):
        with self.client.session_transaction() as session:
            session["user"] = {
                "name": name,
                "email": email
            }

    def given_user_is_not_signed_in(self):
        with self.client.session_transaction() as session:
            if "user" in session:
                del session["user"]

import unittest
from hamcrest import assert_that, is_
from backdrop.write.permissions import Permissions


class PermissionsTestCase(unittest.TestCase):

    def test_return_false_for_unknown_bucket(self):
        permissions = Permissions({})

        assert_that(permissions.allowed("anyuser", "anybucket"), is_(False))

    def test_return_false_for_unauthorised_user(self):
        permissions = Permissions({
            "mybucket": ["userone", "usertwo"]
        })

        assert_that(permissions.allowed("userthree", "mybucket"), is_(False))

    def test_return_true_for_user_in_list_for_bucket(self):
        permissions = Permissions({
            "mybucket": ["userone", "usertwo"]
        })

        assert_that(permissions.allowed("userone", "mybucket"), is_(True  ))

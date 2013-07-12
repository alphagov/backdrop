import unittest
from hamcrest import assert_that, is_
from backdrop.write.permissions import Permissions


class PermissionsTestCase(unittest.TestCase):

    def test_return_false_for_unknown_bucket(self):
        permissions = Permissions({})

        assert_that(permissions.allowed("anyuser", "anybucket"), is_(False))

    def test_return_false_for_unauthorised_user(self):
        permissions = Permissions({
            "userone": ["mybucket"],
            "usertwo": ["mybucket"]
        })

        assert_that(permissions.allowed("userthree", "mybucket"), is_(False))

    def test_return_true_for_user_in_list_for_bucket(self):
        permissions = Permissions({
            "userone": ["mybucket"],
            "usertwo": ["mybucket"]
        })

        assert_that(permissions.allowed("userone", "mybucket"), is_(True))

    def test_returns_list_of_buckets_for_known_user(self):
        permissions = Permissions({
            "userone": ["moj", "fco"],
            "usertwo": ["dvla", "etc"]
        })

        assert_that(permissions.get_buckets_for_user("userone"),
                    is_(["moj", "fco"]))

    def test_returns_empty_list_for_unknown_user(self):
        permissions = Permissions({
            "otheruser": ["foo"]
        })

        assert_that(permissions.get_buckets_for_user("userone"), is_([]))

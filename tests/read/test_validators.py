import unittest
from hamcrest import *
from backdrop.read.validation import ParameterMustBeOneOfTheseValidator

#TODO: looked around and couldn't see any other validator tests


class TestValidators(unittest.TestCase):
    def test_value_must_be_one_of_these_validator(self):
        request = {
            "foo": "not_allowed"
        }
        validator = ParameterMustBeOneOfTheseValidator(
            request_args=request,
            param_name="foo",
            must_be_one_of_these=["bar", "zap"]
        )

        assert_that(validator.invalid(), is_(True))

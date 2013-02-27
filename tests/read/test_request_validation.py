from unittest import TestCase
from hamcrest import assert_that
from read.api import validate_request_args
from tests.support.aborts_with import aborts_with

__author__ = 'mfliri'


class TestRequestValidation(TestCase):
    def test_reject_invalid_start_at(self):
        assert_that(
            lambda: validate_request_args({"start_at": "i am not a time"}),
            aborts_with(400)
        )

    def test_reject_invalid_end_at(self):
        assert_that(lambda: validate_request_args({"end_at": "foo"}),
                    aborts_with(400))

    def test_reject_filter_with_no_colon(self):
        assert_that(
            lambda: validate_request_args({"filter_by": "bar"}),
            aborts_with(400)
        )

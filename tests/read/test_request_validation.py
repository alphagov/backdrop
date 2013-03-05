from unittest import TestCase
from hamcrest import assert_that, is_
from performance_platform.read.api import validate_request_args


class TestRequestValidation(TestCase):
    def test_reject_invalid_start_at(self):
        assert_that(
            validate_request_args({'start_at': 'i am not a time'}).is_valid,
            is_(False)
        )

    def test_reject_invalid_end_at(self):
        assert_that(
            validate_request_args({'end_at': 'foo'}).is_valid,
            is_(False)
        )

    def test_reject_filter_with_no_colon(self):
        assert_that(
            validate_request_args({'filter_by': 'bar'}).is_valid,
            is_(False)
        )

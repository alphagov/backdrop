from unittest import TestCase
from hamcrest import assert_that, is_, instance_of
from backdrop.read.api import validate_request_args


class TestRequestValidation(TestCase):
    def test_reject_invalid_start_at(self):
        assert_that(
            validate_request_args({'start_at': 'i am not a time'}).is_valid,
            is_(False)
        )

    def test_accepts_valid_start_at(self):
        validation_result = validate_request_args({
            'start_at': '2000-02-02T00:02:02+00:00'
        })
        assert_that(validation_result.is_valid, is_(True))

    def test_reject_invalid_end_at(self):
        assert_that(
            validate_request_args({'end_at': 'foo'}).is_valid,
            is_(False)
        )

    def test_accepts_valid_end_at(self):
        validation_result = validate_request_args({
            'end_at': '2000-02-02T00:02:02+00:00'
        })
        assert_that(validation_result.is_valid, is_(True))

    def test_reject_filter_with_no_colon(self):
        assert_that(
            validate_request_args({'filter_by': 'bar'}).is_valid,
            is_(False)
        )

    def test_accepts_valid_filter(self):
        validation_result = validate_request_args({
            'filter_by': 'foo:bar'
        })
        assert_that(validation_result.is_valid, is_(True))

    def test_accepts_period_with_start_at_and_end_at_present(self):
        validation_result = validate_request_args({
            'period': 'week',
            'start_at': '2010-01-01T00:10:10+00:00',
            'end_at': '2010-01-07T00:10:10+00:00',
        })
        assert_that( validation_result.is_valid, is_(True) )

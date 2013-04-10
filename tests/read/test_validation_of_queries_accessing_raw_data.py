from unittest import TestCase
from hamcrest import assert_that, is_
from backdrop.read import api
from backdrop.read.validation import validate_request_args
from tests.support.is_invalid_with_message import is_invalid_with_message


class TestValidationOfQueriesAccessingRawData(TestCase):
    def setUp(self):
        api.app.config['PREVENT_RAW_QUERIES'] = True

    def tearDown(self):
        api.app.config['PREVENT_RAW_QUERIES'] = False

    def test_non_aggregate_queries_are_invalid(self):
        validation_result = validate_request_args({})
        assert_that(validation_result, is_invalid_with_message(
            "querying for raw data is not allowed"))

    def test_period_query_is_valid(self):
        validation_result = validate_request_args({'group_by': 'some_key'})
        assert_that(validation_result.is_valid, is_(True))

    def test_grouped_query_is_valid(self):
        validation_result = validate_request_args({'period': 'week'})
        assert_that(validation_result.is_valid, is_(True))

    def test_that_querying_for_less_than_7_days_is_invalid(self):
        validation_result = validate_request_args({
            'period': 'week',
            'start_at': '2012-01-01T00:00:00Z',
            'end_at': '2012-01-05T00:00:00Z'
        })
        assert_that(validation_result,
                    is_invalid_with_message(
                        'The minimum time span for a query is 7 days'))

    def test_that_querying_for_more_than_7_days_is_valid(self):
        validation_result = validate_request_args({
            'period': 'week',
            'start_at': '2013-04-01T00:00:00Z',
            'end_at': '2013-04-15T00:00:00Z'
        })
        assert_that(validation_result.is_valid,
                    is_(True))

    def test_that_start_at_must_be_on_midnight(self):
        validation_result = validate_request_args({
            'period': 'week',
            'start_at': '2013-04-01T00:00:07Z',
            'end_at': '2013-04-09T00:00:00Z'
        })
        assert_that(validation_result,
                    is_invalid_with_message(
                        'start_at must be a monday midnight'))

    def test_that_start_at_must_be_a_monday(self):
        validation_result = validate_request_args({
            'period': 'week',
            'start_at': '2013-03-31T00:00:00Z',
            'end_at': '2013-04-08T00:00:00Z'
        })
        assert_that(validation_result, is_invalid_with_message(
            'start_at must be a monday midnight'))

    def test_that_end_at_must_be_on_midnight(self):
        validation_result = validate_request_args({
            'period': 'week',
            'start_at': '2013-04-01T00:00:00Z',
            'end_at': '2013-04-08T09:00:09Z'
        })
        assert_that(validation_result,
                    is_invalid_with_message(
                        'end_at must be a monday midnight'))

    def test_that_end_at_must_be_a_monday(self):
        validation_result = validate_request_args({
            'period': 'week',
            'start_at': '2013-04-01T00:00:00Z',
            'end_at': '2013-04-09T00:00:00Z'
        })
        assert_that(validation_result, is_invalid_with_message(
            'end_at must be a monday midnight'))

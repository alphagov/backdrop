from unittest import TestCase
from hamcrest import assert_that
from backdrop.read import api
from backdrop.read.validation import validate_request_args
from tests.support.validity_matcher import is_invalid_with_message, is_valid


class TestValidationOfQueriesAccessingRawData(TestCase):
    def setUp(self):
        api.app.config['PREVENT_RAW_QUERIES'] = True

    def tearDown(self):
        api.app.config['PREVENT_RAW_QUERIES'] = False

    def test_non_aggregate_queries_are_invalid(self):
        validation_result = validate_request_args({})
        assert_that(validation_result, is_invalid_with_message(
            "querying for raw data is not allowed"))

    def test_that_grouped_queries_are_allowed(self):
        validation_result = validate_request_args({'group_by': 'some_key'})
        assert_that(validation_result, is_valid())

    def test_that_periodic_queries_are_allowed(self):
        validation_result = validate_request_args({'period': 'week'})
        assert_that(validation_result, is_valid())

    def test_that_querying_for_less_than_7_days_of_data_is_disallowed(self):
        validation_result = validate_request_args({
            'period': 'week',
            'start_at': '2012-01-01T00:00:00Z',
            'end_at': '2012-01-05T00:00:00Z'
        })
        assert_that(validation_result,
                    is_invalid_with_message(
                        'The minimum time span for a query is 7 days'))

    def test_that_querying_for_more_than_7_days_of_data_is_allowed(self):
        validation_result = validate_request_args({
            'period': 'week',
            'start_at': '2013-04-01T00:00:00Z',
            'end_at': '2013-04-15T00:00:00Z'
        })
        assert_that(validation_result, is_valid())

    def test_that_query_starting_on_midnight_is_allowed(self):
        result = validate_request_args({
            'group_by': 'some_key',
            'start_at': '2013-01-01T00:00:00+00:00'
        })
        assert_that(result, is_valid())

    def test_that_query_ending_on_midnight_is_allowed(self):
        result = validate_request_args({
            'group_by': 'some_key',
            'end_at': '2013-01-31T00:00:00+00:00'
        })
        assert_that(result, is_valid())

    def test_that_period_query_with_monday_limits_is_allowed(self):
        validation_result = validate_request_args({
            'period': 'week',
            'start_at': '2013-04-01T00:00:00Z',
            'end_at': '2013-04-08T00:00:00Z'
        })
        assert_that(validation_result, is_valid())

    def test_that_period_queries_not_starting_on_monday_are_disallowed(self):
        validation_result_not_a_monday = validate_request_args({
            'period': 'week',
            'start_at': '2013-03-31T00:00:00Z',
            'end_at': '2013-04-08T00:00:00Z'
        })
        assert_that(validation_result_not_a_monday, is_invalid_with_message(
            'start_at must be a monday'))

    def test_that_period_queries_not_ending_on_monday_are_disallowed(self):
        validation_result_not_a_monday = validate_request_args({
            'period': 'week',
            'start_at': '2013-04-01T00:00:00Z',
            'end_at': '2013-04-09T00:00:00Z'
        })
        assert_that(validation_result_not_a_monday, is_invalid_with_message(
            'end_at must be a monday'))

    def test_that_start_at_with_time_other_than_midnight_is_disallowed(self):
        validation_result = validate_request_args({
            'group_by': 'some_key',
            'start_at': '2013-04-01T00:00:01Z'
        })
        assert_that(validation_result, is_invalid_with_message(
            'start_at must be midnight'))

    def test_that_end_at_with_time_other_than_midnight_is_disallowed(self):
        validation_result = validate_request_args({
            'group_by': 'some_key',
            'end_at': '2013-04-01T00:00:01Z'
        })
        assert_that(validation_result, is_invalid_with_message(
            'end_at must be midnight'))

    def test_that_queries_which_are_not_midnight_utc_are_disallowed(self):
        validation_result = validate_request_args({
            'group_by': 'some_key',
            'start_at': '2013-04-01T00:00:00+04:30'
        })

        assert_that(validation_result, is_invalid_with_message(
            "start_at must be midnight"
        ))

    def test_that_queries_which_are_midnight_and_not_utc_are_allowed(self):
        validation_result = validate_request_args({
            'group_by': 'some_key',
            'start_at': '2013-04-01T04:30:00+04:30'
        })

        assert_that(validation_result, is_valid())

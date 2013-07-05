from unittest import TestCase
from hamcrest import assert_that, is_
from backdrop.read import validation
from backdrop.read.api import validate_request_args as _validate_request_args
from werkzeug.datastructures import MultiDict
from tests.support.validity_matcher import is_invalid_with_message, is_valid


def validate_request_args(request_args):
    if not isinstance(request_args, MultiDict):
        request_args = MultiDict(request_args)
    return _validate_request_args(request_args, raw_queries_allowed=True)


class TestRequestValidation(TestCase):
    def test_queries_with_badly_formatted_start_at_are_disallowed(self):
        assert_that(
            validate_request_args({
                'start_at': 'i am not a time',
                'end_at': 'i am not a time'
            }),
            is_invalid_with_message("start_at is not a valid datetime")
        )

    def test_queries_with_well_formatted_start_at_are_allowed(self):
        validation_result = validate_request_args({
            'start_at': '2000-02-02T00:02:02+00:00',
            'end_at': '2000-02-09T00:02:02+00:00'
        })
        assert_that(validation_result, is_valid())

    def test_queries_with_badly_formatted_end_at_are_disallowed(self):
        assert_that(
            validate_request_args({
                'start_at': '2000-02-02T00:02:02+00:00',
                'end_at': 'foo'
            }),
            is_invalid_with_message("end_at is not a valid datetime")
        )

    def test_queries_with_well_formatted_end_at_are_allowed(self):
        validation_result = validate_request_args({
            'start_at': '2000-02-02T00:02:02+00:00',
            'end_at': '2000-02-09T00:02:02+00:00'
        })
        assert_that(validation_result, is_valid())

    def test_queries_with_no_colon_in_filter_by_are_disallowed(self):
        validation_result = validate_request_args({
            'filter_by': 'bar'
        })
        assert_that( validation_result, is_invalid_with_message(
            "filter_by must be a field name and value separated by a "
            "colon (:) eg. authority:Westminster"
        ))

    def test_queries_with_well_formatted_filter_by_are_allowed(self):
        validation_result = validate_request_args(MultiDict([
            ('filter_by', 'foo:bar')
        ]))
        assert_that(validation_result, is_valid())

    def test_subsequent_filter_by_parameters_are_validated(self):
        validation_result = validate_request_args(MultiDict([
            ('filter_by', 'foo:bar'),
            ('filter_by', 'bar'),
        ]))
        assert_that(validation_result, is_invalid_with_message(
            "filter_by must be a field name and value separated by a colon "
            "(:) eg. authority:Westminster"
        ))

    def test_queries_filtering_by_invalid_field_names_are_disallowed(self):
        validation_result = validate_request_args({
            'filter_by': 'with-hyphen:bar'
        })
        assert_that(validation_result, is_invalid_with_message(
            'Cannot filter by an invalid field name'
        ))

    def test_queries_with_will_formatted_starts_and_ends_are_allowed(self):
        validation_result = validate_request_args({
            'period': 'week',
            'start_at': '2010-01-01T00:10:10+00:00',
            'end_at': '2010-01-07T00:10:10+00:00',
        })
        assert_that( validation_result, is_valid() )

    def test_queries_with_grouping_on_internal_fields_are_disallowed(self):
        validation_result = validate_request_args({
            "group_by": "_internal"
        })
        assert_that(validation_result, is_invalid_with_message(
            "Cannot group by internal fields, internal fields "
            "start with an underscore"))

    def test_queries_grouping_on_invalid_field_names_are_disallowed(self):
        validation_result = validate_request_args({"group_by": "with-hyphen"})
        assert_that(validation_result, is_invalid_with_message(
            "Cannot group by an invalid field name"
        ))

    def test_queries_with_sort_by_ascending_are_allowed(self):
        validation_result = validate_request_args({
            'sort_by': 'foo:ascending',
        })
        assert_that( validation_result, is_valid() )

    def test_queries_with_sort_by_descending_are_allowed(self):
        validation_result = validate_request_args({
            'sort_by': 'foo:descending',
        })
        assert_that( validation_result, is_valid() )

    def test_queries_with_unrecognized_sort_by_values_are_disallowed(self):
        validation_result = validate_request_args({
            'sort_by': 'foo:random',
        })
        assert_that( validation_result, is_invalid_with_message(
            'Unrecognised sort direction. Supported directions '
            'include: ascending, descending') )

    def test_queries_sorting_by_invalid_field_names_are_disallowed(self):
        validation_result = validate_request_args({
            'sort_by': 'with-hyphen:ascending'
        })
        assert_that(validation_result, is_invalid_with_message(
            'Cannot sort by an invalid field name'
        ))

    def test_queries_with_positive_integer_limit_values_are_allowed(self):
        validation_result = validate_request_args({
            'limit': '3'
        })
        assert_that( validation_result, is_valid() )

    def test_queries_with_non_integer_limit_values_are_disallowed(self):
        validation_result = validate_request_args({
            'limit': 'not_a_number'
        })
        assert_that( validation_result, is_invalid_with_message(
            "limit must be a positive integer"))

    def test_queries_with_a_negative_limit_value_are_disallowed(self):
        validation_result = validate_request_args({
            'limit': '-3'
        })
        assert_that( validation_result, is_invalid_with_message(
            "limit must be a positive integer"))

    def test_queries_with_sort_by_and_period_are_disallowed(self):
        validation_result = validate_request_args({
            "sort_by": "foo:ascending",
            "period": "week"
        })
        assert_that( validation_result, is_invalid_with_message(
            "Cannot sort for period queries without group_by. "
            "Period queries are always sorted by time.") )

    def test_queries_with_sort_by_and_period_and_group_by_are_allowed(self):
        validation_result = validate_request_args({
            "sort_by": "foo:ascending",
            "period": "week",
            "group_by": "foo"
        })
        assert_that( validation_result, is_valid() )

    def test_queries_with_unrecognized_parameters_are_disallowed(self):
        validation_result = validate_request_args({
            "unrecognised_parameter": "value"
        })
        assert_that( validation_result, is_invalid_with_message(
            "An unrecognised parameter was provided"))

    def test_queries_with_collect_and_group_by_are_allowed(self):
        validation_result_with_group_by = validate_request_args(MultiDict([
            ("collect", 'foo'),
            ("group_by", 'bar')
        ]))
        assert_that(validation_result_with_group_by, is_valid())

    def test_queries_with_collect_and_no_group_by_are_disallowed(self):
        validation_result_without_group_by = validate_request_args(MultiDict([
            ("collect", 'foo')
        ]))
        assert_that(validation_result_without_group_by,
                    is_invalid_with_message(
                        'collect can be use only with group_by'))

    def test_queries_without_code_injection_collect_values_are_allowed(self):
        validation_result_without_group_by = validate_request_args(MultiDict([
            ("group_by", 'bar'),
            ("collect", 'a_aAbBzZ_')
        ]))
        assert_that(validation_result_without_group_by, is_valid())

    def test_queries_with_code_injection_collect_values_are_disallowed(self):
        validation_result_without_group_by = validate_request_args(MultiDict([
            ("group_by", 'bar'),
            ("collect", 'something);while(1){myBadFunction()}')
        ]))
        assert_that(validation_result_without_group_by,
                    is_invalid_with_message(
                        "Cannot collect an invalid field name"))

    def test_queries_collecting_invalid_field_names_are_disallowed(self):
        validation_result = validate_request_args(MultiDict([
            ("group_by", "bar"),
            ("collect", "with-hyphen")
        ]))
        assert_that(validation_result, is_invalid_with_message(
            "Cannot collect an invalid field name"
        ))

    def test_queries_with_multiple_collect_values_as_code_are_disallowed(self):
        validation_result_without_group_by = validate_request_args(MultiDict([
            ("group_by", 'bar'),
            ("collect", '$foo'),
            ("collect", 'foo'),
        ]))
        assert_that(validation_result_without_group_by,
                    is_invalid_with_message(
                        "Cannot collect an invalid field name"))

    def test_subsequent_collect_values_are_validated(self):
        validation_result = validate_request_args(MultiDict([
            ("group_by", "foo"),
            ("collect", "bar"),
            ("collect", "{}"),
        ]))
        assert_that(validation_result,
                    is_invalid_with_message(
                        "Cannot collect an invalid field name"))

    def test_queries_with_internal_collect_values_are_disallowed(self):
        validation_result_without_group_by = validate_request_args(MultiDict([
            ("group_by", 'bar'),
            ("collect", '_internal_field')
        ]))
        assert_that(validation_result_without_group_by,
                    is_invalid_with_message("Cannot collect internal fields, "
                                            "internal fields start "
                                            "with an underscore"))

    def test_queries_grouping_and_collecting_equal_fields_are_disallowed(self):
        validation_result_without_group_by = validate_request_args(MultiDict([
            ("group_by", 'a_field'),
            ("collect", 'a_field')
        ]))
        assert_that(validation_result_without_group_by,
                    is_invalid_with_message(
                        "Cannot collect by a field that is used for group_by"))

    def test_queries_grouping_week_start_at_with_period_are_disallowed(self):
        validation_result = validate_request_args({
            'period': 'week',
            'group_by': '_week_start_at'
        })

        assert_that(validation_result, is_invalid_with_message(
            "Cannot group by internal fields, internal fields "
            "start with an underscore"))

    def test_queries_with_period_values_must_be_certain_values(self):
        validation_result = validate_request_args({
            'period': 'fortnight'
        })

        assert_that(validation_result, is_invalid_with_message(
            "'period' must be one of ['week', 'month']"))

    def test_queries_without_a_colon_in_sort_by_are_disallowed(self):
        validation_result = validate_request_args({
            'sort_by': 'lulz'
        })

        assert_that(validation_result, is_invalid_with_message(
            'sort_by must be a field name and sort direction separated '
            'by a colon (:) eg. authority:ascending'))

    def test_queries_collecting_internal_fields_are_disallowed(self):
        validation_result = validate_request_args(MultiDict([
            ('group_by', 'not_walruses'),
            ('collect', '_walrus')
        ]))

        assert_that(validation_result, is_invalid_with_message(
            'Cannot collect internal fields, internal fields start '
            'with an underscore'))

    def test_queries_with_non_existent_dates_are_disallowed(self):
        validation_result = validate_request_args({
            'start_at': '2013-13-70T00:00:00Z',
            'end_at': '2013-12-70T00:00:00Z'
        })

        assert_that(validation_result, is_invalid_with_message(
            "start_at is not a valid datetime"))

    def test_that_queries_with_invalid_timezone_are_disallowed(self):
        validation_result = validate_request_args({
            'start_at': '2013-01-01T00:00:00+24:00',
            'end_at': '2013-01-08T00:00:00+24:00'
        })

        assert_that(validation_result, is_invalid_with_message(
            "start_at is not a valid datetime"))

    def test_that_collect_queries_with_valid_methods_are_allowed(self):
        valid_collection_methods = ["sum", "count", "set", "mean"]

        for method in valid_collection_methods:
            validation_result = validate_request_args({
                'group_by': 'foo',
                'collect': 'field:{0}'.format(method),
            })

            assert_that(validation_result, is_valid())

    def test_that_collect_queries_with_invalid_method_are_disallowed(self):
        validation_result = validate_request_args({
            'group_by': 'foo',
            'collect': 'field:infinity',
        })

        assert_that(validation_result, is_invalid_with_message((
            "Unknown collection method"
        )))


class TestValidationHelpers(TestCase):
    def test_timestamp_is_valid_method(self):
        result = validation.value_is_valid_datetime_string(
            "2013-01-01T00:00:00+99:99")

        assert_that(result, is_(False))

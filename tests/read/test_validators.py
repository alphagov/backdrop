import unittest
from hamcrest import *
from backdrop.read.validation import ParameterMustBeOneOfTheseValidator, MondayValidator, FirstOfMonthValidator, ParamDependencyValidator

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

    def test_monday_validator_only_validates_when_period_is_week(self):
        period_week_request = {
            "period": "week",
            "_start_at": "2013-01-02T00:00:00+00:00"
        }

        period_month_request = {
            "period": "month",
            "_start_at": "2013-01-02T00:00:00+00:00"
        }

        i_should_be_invalid = MondayValidator(
            request_args=period_week_request,
            param_name="_start_at"
        )

        i_should_be_valid = MondayValidator(
            request_args=period_month_request,
            param_name="_start_at"
        )

        assert_that(i_should_be_invalid.invalid(), is_(True))
        assert_that(i_should_be_valid.invalid(), is_(False))

    def test_first_of_month_validator_only_validates_for_period_month(self):
        period_week_request = {
            "period": "week",
            "_start_at": "2013-01-02T00:00:00+00:00"
        }

        period_month_request = {
            "period": "month",
            "_start_at": "2013-01-02T00:00:00+00:00"
        }

        i_should_be_invalid = FirstOfMonthValidator(
            request_args=period_month_request,
            param_name="_start_at"
        )

        i_should_be_valid = FirstOfMonthValidator(
            request_args=period_week_request,
            param_name="_start_at"
        )

        assert_that(i_should_be_invalid.invalid(), is_(True))
        assert_that(i_should_be_valid.invalid(), is_(False))

    def test_param_dependency_validator(self):
        query = {
            "collect": "foo",
            "group_by": "test"
        }

        validator = ParamDependencyValidator(request_args=query,
                                             param_name="collect",
                                             depends_on=["group_by"])
        assert_that(validator.invalid(), is_(False))

    def test_param_dependency_validator_invalidates_correctly(self):
        query = {
            "collect": "foo",
            "group_by": "test"
        }

        validator = ParamDependencyValidator(request_args=query,
                                             param_name="collect",
                                             depends_on=["wibble"])
        assert_that(validator.invalid(), is_(True))

    def test_that_a_parameter_can_have_multiple_dependencies(self):
        query = {
            "collect": "foo",
            "period": "week"
        }

        validator = ParamDependencyValidator(request_args=query,
                                             param_name="collect",
                                             depends_on=["group_by", "period"])
        assert_that(validator.invalid(), is_(False))

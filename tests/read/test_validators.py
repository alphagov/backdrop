import unittest
from hamcrest import *
from backdrop.read.validation import ParameterMustBeOneOfTheseValidator, MondayValidator, FirstOfMonthValidator

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

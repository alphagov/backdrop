from hamcrest.core.base_matcher import BaseMatcher


class ValidityMatcher(BaseMatcher):
    def __init__(self, valid, message=None):
        self.expect_valid = valid
        self.expected_message = message

    def _matches(self, validation_result):
        if self.expect_valid:
            return validation_result.is_valid

        return not validation_result.is_valid \
            and validation_result.message == self.expected_message

    def describe_to(self, description):
        description.append_text(self._description(self.expect_valid, self.expected_message))

    def describe_mismatch(self, validation_result, mismatch_description):
        mismatch_description.append_text(self._description(validation_result.is_valid, validation_result.message))

    def _description(self, valid, message):
        if valid:
            return "valid"
        return "invalid validation with message: {message}".format(
            message=message
        )


def is_invalid_with_message(message):
    return ValidityMatcher(False, message)


def is_valid():
    return ValidityMatcher(True)

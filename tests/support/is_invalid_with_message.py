from hamcrest.core.base_matcher import BaseMatcher


class IsInvalidWithMessage(BaseMatcher):
    def __init__(self, message):
        self.expected_message = message

    def _matches(self, validation_result):
        if validation_result.is_valid:
            return False

        return validation_result.message == self.expected_message

    def describe_to(self, description):
        description.append_text(
            "invalid validation with message: {message}".format(
                message=self.expected_message
            )
        )

    def describe_mismatch(self, validation_result, mismatch_description):
        if validation_result.is_valid:
            mismatch_description.append_text("valid")
        else:
            mismatch_description.append_text(
                "invalid validation with message: {message}".format(
                    message=validation_result.message
                )
            )


def is_invalid_with_message(message):
    return IsInvalidWithMessage(message)

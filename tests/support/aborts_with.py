from hamcrest.core.base_matcher import BaseMatcher
from werkzeug import exceptions


class AbortsWithCode(BaseMatcher):
    def __init__(self, http_status_code):
        self.expected_status_code = http_status_code

    def _matches(self, a_lambda):
        try:
            a_lambda()
            return False
        except exceptions.HTTPException as e:
            return e.code == self.expected_status_code

    def describe_to(self, description):
        description.append_text(
            "HTTPException with status {code}".format(
                code = self.expected_status_code
            )
        )

    def describe_mismatch(self, item, mismatch_description):
        mismatch_description.append_text("no exception was raised")


def aborts_with(status_code):
    return AbortsWithCode(status_code)

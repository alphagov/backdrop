import unittest
from hamcrest import assert_that, is_
from nose.tools import raises
import werkzeug
from backdrop.core.flaskutils import BucketConverter


class BucketConverterTestCase(unittest.TestCase):

    def setUp(self):
        self.converter = BucketConverter(None)

    def test_returns_when_uri_variable_is_a_valid_data_set_name(self):
        p = self.converter.to_python("valid_data_set_name")

        assert_that(p, is_("valid_data_set_name"))

    @raises(werkzeug.routing.ValidationError)
    def test_raises_validation_error_uri_variable_is_invalid_data_set_name(self):
        self.converter.to_python("$invalid_data_set_name")

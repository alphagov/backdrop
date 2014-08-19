from base64 import b64encode
import unittest
from hamcrest import assert_that, contains, has_entry, is_, is_not, has_key
from nose.tools import raises
from backdrop.core.records import add_auto_ids
from backdrop.core.errors import ValidationError


class TestDataSetAutoIdGeneration(unittest.TestCase):
    def test_auto_id_for_a_single_field(self):
        records = [{'abc': 'def'}]

        result, errors = add_auto_ids(records, ['abc'])

        assert_that(
            result,
            contains(
                is_({'_id': b64encode('def'), 'abc': 'def'})))

    def test_auto_id_generation(self):
        records = [{
            "postcode": "WC2B 6SE",
            "number": "125",
            "name": "Aviation House"
        }]

        result, errors = add_auto_ids(records, ['postcode', 'number'])

        assert_that(
            result,
            contains(
                has_entry('_id', b64encode('WC2B 6SE.125'))))
        assert_that(
            errors, is_([]))

    def test_no_id_generated_if_auto_id_is_none(self):
        records = [{
            "postcode": "WC2B 6SE",
            "number": "125",
            "name": "Aviation House"
        }]

        result, errors = add_auto_ids(records, None)

        assert_that(
            result,
            contains(
                is_not(has_key('_id'))))

    def test_errors_if_auto_id_property_is_missing(self):
        records = [{
            "postcode": "WC2B 6SE",
            "name": "Aviation House"
        }]

        # call list to evaluate generator
        results, errors = add_auto_ids(records, ['postcode', 'number'])
        assert_that(
            errors,
            contains(
                'The following required id fields are missing: number'))

    def test_auto_id_can_be_generated_from_a_timestamp(self):
        records = [{
            "_timestamp": "2013-08-01T00:00:00+00:00",
            "foo": "bar"
        }]

        result, errors = add_auto_ids(records, ['_timestamp', 'foo'])

        assert_that(
            result,
            contains(
                has_entry('_id', b64encode('2013-08-01T00:00:00+00:00.bar'))))

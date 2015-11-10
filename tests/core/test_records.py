from unittest import TestCase
from hamcrest import assert_that, is_, equal_to
from nose.tools import assert_raises
from backdrop.core.records import _generate_auto_id, \
    make_query_criteria_from_auto_ids
from backdrop.core.errors import ValidationError


class TestRecords(TestCase):
    def test__generate_auto_id_generates_auto_ids_correctly_for_standard_case(self):
        assert_that(_generate_auto_id({'foo': 'foo'}, ['foo']), is_('Zm9v'))

    def test__generate_auto_id_generates_auto_ids_correctly_for_integers(self):
        assert_that(_generate_auto_id({'foo': 1, 'bar': 'foo'}, ['foo', 'bar']), is_('MS5mb28='))

    def test__generate_auto_id_throws_error_when_key_not_matched(self):
        assert_raises(
            ValidationError,
            _generate_auto_id,
            {'foo': 1},
            ['bar'])

    def test_make_query_criteria(self):
        auto_id_keys = ['_timestamp', 'channel']
        new_record = {
            "_timestamp": "12-12-2012 00:00:00",
            "count": 3,
            "channel": "paper"
        }

        expected_query_criteria = {
            "_timestamp": "12-12-2012 00:00:00",
            "channel": "paper"
        }

        assert_that(make_query_criteria_from_auto_ids(
            new_record, auto_id_keys), equal_to(expected_query_criteria))

from unittest import TestCase
from hamcrest import assert_that, is_
from nose.tools import assert_raises
from backdrop.core.records import _generate_auto_id
from backdrop.core.errors import ValidationError


class TestRecords(TestCase):
    def test__generate_auto_id_generates_auto_ids_correctly_for_standard_case(self):
        assert_that(_generate_auto_id({'foo': 'foo'}, ['foo']), is_('Zm9v'))

    def test__generate_auto_id_generates_auto_ids_correctly_for_integers(self):
        assert_that(_generate_auto_id({'foo': 1}, ['foo']), is_('Zm9v'))

    def test__generate_auto_id_throws_error_when_key_not_matched(self):
        assert_raises(
            ValidationError,
            _generate_auto_id,
            {'foo': 1},
            ['bar'])

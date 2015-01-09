import unittest

from hamcrest import assert_that, is_

from backdrop.transformers.tasks.util import encode_id, group_by


class UtilTestCase(unittest.TestCase):
    def test_encode_id(self):
        assert_that(
            encode_id('foo', 'bar'),
            is_('Zm9vX2Jhcg==')
        )

    def test_group_by(self):
        groupped_data = group_by(['a', 'b'], [
            {
                'a': 'foo',
                'b': 'bar',
            },
            {
                'a': 'foo',
                'b': 'bar',
            },
            {
                'a': 'foo',
                'b': 'foo',
            },
        ])

        assert_that(len(groupped_data.keys()), is_(2))
        assert_that(len(groupped_data[('foo', 'bar')]), is_(2))
        assert_that(len(groupped_data[('foo', 'foo')]), is_(1))

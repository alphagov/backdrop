import unittest

from hamcrest import assert_that, is_

from backdrop.transformers.tasks.util import encode_id


class UtilTestCase(unittest.TestCase):
    def test_encode_id(self):
        assert_that(
            encode_id('foo', 'bar'),
            is_('Zm9vX2Jhcg==')
        )

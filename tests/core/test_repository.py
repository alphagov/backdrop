import unittest
from hamcrest import assert_that, is_
from backdrop.core.repository import nested_merge


class NestedMergeTestCase(unittest.TestCase):
    def test_nested_merge_merges_two_dictionaries(self):
        result = nested_merge({}, ['a', 'b'], {'a': 1, 'b': 2, 'c': 3})
        assert_that(result, is_({1: {2: {'c': 3}}}))

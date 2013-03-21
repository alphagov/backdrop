import unittest
from hamcrest import assert_that, is_
from backdrop.core.repository import nested_merge


class NestedMergeTestCase(unittest.TestCase):
    def test_nested_merge_merges_dictionaries(self):
        dictionaries = [
            {'a': 1, 'b': 2, 'c': 3},
            {'a': 1, 'b': 1, 'c': 3},
        ]

        output = nested_merge(['a', 'b'], dictionaries)
        assert_that(output, is_({1: {2: {'c': 3}, 1: {'c': 3}}}))

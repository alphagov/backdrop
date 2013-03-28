import unittest
from hamcrest import assert_that, is_, instance_of
from backdrop.core import database
from backdrop.core.database import Repository


class NestedMergeTestCase(unittest.TestCase):
    def setUp(self):
        self.dictionaries = [
            {'a': 1, 'b': 2, 'c': 3},
            {'a': 1, 'b': 1, 'c': 3},
            {'a': 2, 'b': 1, 'c': 3}
        ]

    def test_nested_merge_merges_dictionaries(self):

        output = database.nested_merge(['a', 'b'], self.dictionaries)
        assert_that(output, is_([
            {
                "a": 1,
                "_subgroup": [
                    {
                        "b": 2,
                        "c": 3
                    },
                    {
                        "b": 1,
                        "c": 3
                    }
                ]
            },
            {
                "a": 2,
                "_subgroup": [
                    {
                        "b": 1,
                        "c": 3
                    }
                ]
            }
        ]))

    def test_nested_merge_squashes_duplicates(self):
        output = database.nested_merge(['a'], self.dictionaries)
        assert_that(output, is_([
            {'a': 1, 'b': 2, 'c': 3},
            {'a': 2, 'b': 1, 'c': 3}
        ]))

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = database.Database('localhost', 27017, 'backdrop_test')

    def test_alive(self):
        assert_that(self.db.alive(), is_(True))

    def test_getting_a_repository(self):
        repository = self.db.get_repository('my_bucket')
        assert_that(repository, instance_of(Repository))
        assert_that(repository.name, 'my_bucket')

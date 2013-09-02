import unittest
from hamcrest import assert_that, is_, contains, has_entries
from backdrop.core.nested_merge import reduce_collected_values, InvalidOperationError, nested_merge, group_by
from backdrop.core.timeseries import WEEK, MONTH


def datum(name=None, place=None, age=None, stamp=None, count=1):
    result = {
        "_count": count
    }
    if name is not None:
        result['name'] = name
    if place is not None:
        result['place'] = place
    if age is not None:
        result['age'] = age
    if stamp is not None:
        result['_timestamp'] = stamp
        result['_week_start_at'] = WEEK.start(stamp)
        result['_month_start_at'] = MONTH.start(stamp)
    return result


class TestNestedMerge(object):

    def test_one_level_grouping_with_collect(self):
        data = [
            datum(name='Jill', age=[12, 45]),
            datum(name='Jack', age=[34, 34]),
            datum(name='John', age=[56, 65])
        ]
        results = nested_merge(['name'], [('age', 'mean')], data)

        assert_that(results,
                    contains(
                        has_entries({'name': 'Jack', 'age:mean': 34}),
                        has_entries({'name': 'Jill', 'age:mean': 28.5}),
                        has_entries({'name': 'John', 'age:mean': 60.5}),
                    ))

    def test_two_level_grouping_with_collect(self):
        data = [
            datum(name='Jill', place='Kettering', age=[34, 36], count=2),
            datum(name='Jack', place='Kennington', age=[23], count=1),
            datum(name='James', place='Keswick', age=[10, 21, 32], count=3),
            datum(name='James', place='Kettering', age=[43, 87], count=2),
            datum(name='Jill', place='Keswick', age=[76, 32], count=2),
        ]
        results = nested_merge(['name', 'place'], [('age', 'mean')], data)

        assert_that(results,
                    contains(
                        has_entries({
                            'name': 'Jack',
                            'age:mean': 23,
                            '_subgroup': contains(
                                has_entries({
                                    'place': 'Kennington',
                                    'age:mean': 23
                                })
                            )}),
                        has_entries({
                            'name': 'James',
                            'age:mean': 38.6,
                            '_subgroup': contains(
                                has_entries({
                                    'place': 'Keswick',
                                    'age:mean': 21.0
                                }),
                                has_entries({
                                    'place': 'Kettering',
                                    'age:mean': 65.0
                                })
                            )
                        }),
                        has_entries({
                            'name': 'Jill',
                            'age:mean': 44.5,
                            '_subgroup': contains(
                                has_entries({
                                    'place': 'Keswick',
                                    'age:mean': 54.0
                                }),
                                has_entries({
                                    'place': 'Kettering',
                                    'age:mean': 35.0
                                })
                            )
                        }),
                    ))


class TestGroupBy(object):
    def test_one_level_grouping(self):
        data = [
            datum(name='Jill', age=[12, 45]),
            datum(name='Jack', age=[34, 34]),
            datum(name='John', age=[56, 65])
        ]
        results = group_by(data, ['name'])

        assert_that(results,
                    contains(
                        is_({'name': 'Jack', 'age': [34, 34], '_count': 1}),
                        is_({'name': 'Jill', 'age': [12, 45], '_count': 1}),
                        is_({'name': 'John', 'age': [56, 65], '_count': 1}),
                    ))

    def test_two_level_grouping(self):
        data = [
            datum(name='Jill', place='Kettering', age=[34, 36], count=2),
            datum(name='James', place='Kettering', age=[43, 87], count=2),
            datum(name='Jill', place='Keswick', age=[76, 32], count=2),
        ]
        results = group_by(data, ['name', 'place'])

        assert_that(results,
                    contains(
                        is_({
                            'name': 'James',
                            '_subgroup': [
                                {'place': 'Kettering', 'age': [43, 87], '_count': 2}
                            ]}),
                        is_({
                            'name': 'Jill',
                            '_subgroup': [
                                {'place': 'Keswick', 'age': [76, 32], '_count': 2},
                                {'place': 'Kettering', 'age': [34, 36], '_count': 2},
                            ]}),
                    ))


# TODO
class TestApplyCollectToGroup(object):
    pass


class TestCollectAllValues(object):
    pass


class TestRemoveCollectedKey(object):
    pass


class TestReduceCollectedValues(unittest.TestCase):
    def test_sum(self):
        data = [2, 5, 8]
        response = reduce_collected_values(data, "sum")
        assert_that(response, is_(15))

    def test_count(self):
        data = ['Sheep', 'Elephant', 'Wolf', 'Dog']
        response = reduce_collected_values(data, "count")
        assert_that(response, is_(4))

    def test_set(self):
        data = ['Badger', 'Badger', 'Badger', 'Snake']
        response = reduce_collected_values(data, "set")
        assert_that(response, is_(['Badger', 'Snake']))

    def test_mean(self):
        data = [13, 19, 15, 2]
        response = reduce_collected_values(data, "mean")
        assert_that(response, is_(12.25))

    def test_unknown_collection_method_raises_error(self):
        self.assertRaises(ValueError,
                          reduce_collected_values, ['foo'], "unknown")

    def test_bad_data_for_sum_raises_error(self):
        self.assertRaises(InvalidOperationError,
                          reduce_collected_values, ['sum', 'this'], "sum")

    def test_bad_data_for_mean_raises_error(self):
        self.assertRaises(InvalidOperationError,
                          reduce_collected_values, ['average', 'this'], "mean")

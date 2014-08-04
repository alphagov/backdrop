from hamcrest import assert_that, is_, contains, has_entries, has_entry
from backdrop.core.nested_merge import nested_merge, group_by, \
    apply_collect_to_group, collect_all_values
from backdrop.core.timeseries import WEEK, MONTH


def datum(name=None, version=None, place=None, age=None, stamp=None, count=1):
    result = {
        "_count": count
    }
    if name is not None:
        result['name'] = name
    if version is not None:
        result['version'] = version
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
        results = nested_merge([['name']], [('age', 'mean')], data)

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
        results = nested_merge([['name'], ['place']], [('age', 'mean')], data)

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

    def test_two_level_grouping_combination_of_keys(self):
        data = [
            datum(name='IE', version='6', place='England', age=[13, 12], count=2),
            datum(name='IE', version='6', place='Wales', age=[13, 14], count=2),
            datum(name='IE', version='7', place='England', age=[8, 7], count=2),
            datum(name='IE', version='7', place='Wales', age=[8, 9], count=2),
            datum(name='IE', version='8', place='England', age=[5, 4], count=2),
            datum(name='IE', version='8', place='Wales', age=[5, 6], count=2),
            datum(name='Chrome', version='20', place='England', age=[2, 1], count=2),
            datum(name='Chrome', version='20', place='Wales', age=[2, 3], count=2),
        ]
        results = nested_merge([['name', 'version'], ['place']], [('age', 'mean')], data)

        assert_that(results,
                    contains(
                        has_entries({
                            'name': 'Chrome',
                            'version': '20',
                            'age:mean': 2,
                            '_subgroup': contains(
                                has_entries({
                                    'place': 'England',
                                    'age:mean': 1.5
                                }),
                                has_entries({
                                    'place': 'Wales',
                                    'age:mean': 2.5
                                })
                            )
                        }),
                        has_entries({
                            'name': 'IE',
                            'version': '6',
                            'age:mean': 13,
                            '_subgroup': contains(
                                has_entries({
                                    'place': 'England',
                                    'age:mean': 12.5
                                }),
                                has_entries({
                                    'place': 'Wales',
                                    'age:mean': 13.5
                                })
                            )
                        }),
                        has_entries({
                            'name': 'IE',
                            'version': '7',
                            'age:mean': 8,
                            '_subgroup': contains(
                                has_entries({
                                    'place': 'England',
                                    'age:mean': 7.5
                                }),
                                has_entries({
                                    'place': 'Wales',
                                    'age:mean': 8.5
                                })
                            )
                        }),
                        has_entries({
                            'name': 'IE',
                            'version': '8',
                            'age:mean': 5,
                            '_subgroup': contains(
                                has_entries({
                                    'place': 'England',
                                    'age:mean': 4.5
                                }),
                                has_entries({
                                    'place': 'Wales',
                                    'age:mean': 5.5
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
        results = group_by(data, [['name']])

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
        results = group_by(data, [['name'], ['place']])

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


class TestApplyCollectToGroup(object):
    def test_single_level_collect_sum(self):
        group = {'name': 'Joanne', 'age': [34, 56]}

        assert_that(apply_collect_to_group(group, [('age', 'sum')]),
                    has_entry('age:sum', 90))

    def test_single_level_collect_default(self):
        group = {'name': 'Joanne', 'age': [34, 56]}

        assert_that(apply_collect_to_group(group, [('age', 'default')]),
                    is_({
                        'name': 'Joanne', 'age:set': [34, 56], 'age': [34, 56]}))

    def test_double_level_collect_sum(self):
        group = {'name': 'Joanne', '_subgroup': [
            {'place': 'Kettering', 'age': [34, 56]},
            {'place': 'Keswick', 'age': [87, 2]},
        ]}

        collected = apply_collect_to_group(group, [('age', 'sum')])

        # level one
        assert_that(collected, has_entry('age:sum', 179))
        # level two
        assert_that(collected, has_entry('_subgroup',
                                         contains(
                                             has_entry('age:sum', 90),
                                             has_entry('age:sum', 89)
                                         )))

    def test_double_level_collect_default(self):
        group = {'name': 'Joanne', '_subgroup': [
            {'place': 'Kettering', 'age': [34, 56]},
            {'place': 'Keswick', 'age': [87, 2]},
        ]}

        collected = apply_collect_to_group(group, [('age', 'default')])

        assert_that(collected, has_entries({
            'age:set': [2, 34, 56, 87],
            'age': [2, 34, 56, 87],
        }))

        assert_that(collected, has_entry('_subgroup',
                                         contains(
                                             has_entries({
                                                 'age:set': [34, 56],
                                                 'age': [34, 56],
                                             }),
                                             has_entries({
                                                 'age:set': [2, 87],
                                                 'age': [2, 87],
                                             }),
                                         )))


class TestCollectAllValues(object):
    def test_single_level_collect(self):
        group = {
            'age': [5]
        }
        assert_that(collect_all_values(group, 'age'), [5])

    def test_double_level_collect(self):
        group = {
            'age': [5],  # This will be discarded as there are sub groups.
            '_subgroup': [
                {'age': [1, 2]},
                {'age': [3, 4]},
            ]
        }
        assert_that(collect_all_values(group, 'age'), [1, 2, 3, 4])

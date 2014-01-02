from operator import itemgetter, add
import itertools


def nested_merge(keys, collect, data):
    if len(keys) > 1:
        data = group_by(data, keys)
        data = apply_counts(data)

    data = apply_collect(data, collect)
    data = sort_all(data, keys)

    return data


def group_by(data, keys):
    """Recursively group an array of results by a list of keys

    data: a list of dictionaries as returned by MongoDriver.group
    keys: a list of keys to group by
    """
    key = keys[0]
    getter = itemgetter(key)
    data = sorted(data, key=getter)
    if len(keys) > 1:
        data = [
            {
                key: value,
                "_subgroup": group_by(
                    remove_key_from_all(subgroups, key),
                    keys[1:]
                )
            }
            for value, subgroups in itertools.groupby(data, getter)
        ]
    return data


def remove_key_from_all(groups, key):
    """Remove a key from each group in a list of groups

    groups: a list of groups (dictionaries)
    key: the key to remove
    """
    return [remove_key(group, key) for group in groups]


def remove_key(doc, key):
    """Return a new document with the key removed

    >>> doc = {'a':1, 'b':2}
    >>> remove_key(doc, 'a')
    {'b': 2}
    >>> # Show that the original document is not affected
    >>> doc['a']
    1
    """
    return dict(
        (k, v) for k, v in doc.items() if k != key)


def apply_counts(groups):
    """Add the _count and _group_count fields to a list of groups"""
    return [
        apply_counts_to_group(group)
        for group in groups
    ]


def apply_counts_to_group(group):
    """Add the _count and _group_count fields to a group"""
    if '_subgroup' in group:
        subgroups = apply_counts(group['_subgroup'])
        group['_subgroup'] = subgroups
        group['_count'] = sum(subgroup['_count'] for subgroup in subgroups)
        group['_group_count'] = len(subgroups)
    return group


def apply_collect(groups, collect):
    """Apply collected values to a list of groups

    groups: a list of groups (dictionaries)
    collect: a list of collect fields, each being a tuple of field name and
             collection method
    """
    return [
        apply_collect_to_group(group, collect)
        for group in groups
    ]


def apply_collect_to_group(group, collect):
    group = group.copy()
    # calculate collected values
    for key, method in collect:
        group[collect_key(key, method)] = collect_value(group, key, method)

    # apply collect to subgroups
    if '_subgroup' in group:
        group['_subgroup'] = apply_collect(group['_subgroup'], collect)

    # remove left over collect keys
    for key, _ in collect:
        group = remove_key(group, key)

    # Hack in the old way
    for key, method in collect:
        if method == 'default':
            group[key] = group[collect_key(key, method)]
    return group


def replace_default_method(method):
    return "set" if method == "default" else method


def collect_key(key, method):
    """Return the key for a given collect field and method

    >>> collect_key("foo", "sum")
    'foo:sum'
    >>> collect_key("foo", "default")
    'foo:set'
    """
    return '{0}:{1}'.format(key, replace_default_method(method))


def collect_value(group, key, method):
    reducer = collect_reducer(method)
    return reducer(collect_all_values(group, key))


def collect_all_values(group, key):
    if key in group:
        return group[key]
    elif '_subgroup' in group:
        _subgroup = [
            collect_all_values(sub, key) for sub in group['_subgroup']]
        return reduce(add, _subgroup)


def collect_reducer(method):
    """Return a collector function to be applied over a list of values"""
    method = replace_default_method(method)
    try:
        return globals()['collect_reducer_{}'.format(method)]
    except KeyError:
        raise ValueError(
            "Unknown collection method {}".format(method))


def collect_reducer_sum(values):
    """Return the sum of all values

    >>> collect_reducer_sum([2, 5, 8])
    15
    >>> collect_reducer_sum(['sum', 'this'])
    Traceback (most recent call last):
        ...
    InvalidOperationError: Unable to sum that data
    """
    try:
        return sum(values)
    except TypeError:
        raise InvalidOperationError("Unable to sum that data")


def collect_reducer_count(values):
    """Return the number of values

    >>> collect_reducer_count(['Sheep', 'Elephant', 'Wolf', 'Dog'])
    4
    """
    return len(values)


def collect_reducer_set(values):
    """Return the set of values

    >>> collect_reducer_set(['Badger', 'Badger', 'Badger', 'Snake'])
    ['Badger', 'Snake']
    """
    return sorted(list(set(values)))


def collect_reducer_mean(values):
    """Return the mean of numeric values

    >>> collect_reducer_mean([13, 19, 15, 2])
    12.25
    >>> collect_reducer_mean(['average', 'this'])
    Traceback (most recent call last):
        ...
    InvalidOperationError: Unable to find the mean of that data
    """
    try:
        return sum(values) / float(len(values))
    except TypeError:
        raise InvalidOperationError("Unable to find the mean of that data")


def sort_all(data, keys):
    if len(keys) > 1:
        for i, group in enumerate(data):
            data[i]['_subgroup'] = sort_all(group['_subgroup'], keys[1:])
    return sorted(data, key=itemgetter(keys[0]))


class InvalidOperationError(TypeError):
    pass

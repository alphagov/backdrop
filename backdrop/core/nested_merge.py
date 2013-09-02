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
    """Recursively group an array of results by a list of keys"""
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
    return [remove_key(group, key) for group in groups]


def remove_key(doc, key):
    del doc[key]
    return doc


def apply_counts(data):
    return [
        apply_counts_to_group(group)
        for group in data
    ]


def apply_counts_to_group(group):
    if '_subgroup' in group:
        subgroups = apply_counts(group['_subgroup'])
        group['_subgroup'] = subgroups
        group['_count'] = sum(subgroup['_count'] for subgroup in subgroups)
        group['_group_count'] = len(subgroups)
    return group


def apply_collect(data, collect):
    return [
        apply_collect_to_group(group, collect)
        for group in data
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
        group = remove_collected_key(group, key)

    # Hack in the old way
    for key, method in collect:
        if method == 'default':
            group[key] = group[collect_key(key, method)]
    return group


def collect_key(key, method):
    if method == 'default':
        method = 'set'
    return '{}:{}'.format(key, method)


def collect_value(group, key, method):
    return reduce_collected_values(collect_all_values(group, key), method)


def collect_all_values(group, key):
    collect_values_for_key = lambda subgroup: collect_all_values(subgroup, key)
    if key in group:
        return group[key]
    elif '_subgroup' in group:
        return reduce(add, map(collect_values_for_key, group['_subgroup']))


def reduce_collected_values(values, method):
    if "sum" == method:
        try:
            return sum(values)
        except TypeError:
            raise InvalidOperationError("Unable to sum that data")
    elif "count" == method:
        return len(values)
    elif "set" == method:
        return sorted(list(set(values)))
    elif "mean" == method:
        try:
            return sum(values) / float(len(values))
        except TypeError:
            raise InvalidOperationError("Unable to find the mean of that data")
    elif "default" == method:
        return reduce_collected_values(values, "set")
    else:
        raise ValueError("Unknown collection method")


def remove_collected_key(group, key):
    if key in group:
        del group[key]
    return group


def sort_all(data, keys):
    if len(keys) > 1:
        for i, group in enumerate(data):
            data[i]['_subgroup'] = sort_all(group['_subgroup'], keys[1:])
    return sorted(data, key=itemgetter(keys[0]))


class InvalidOperationError(TypeError):
    pass

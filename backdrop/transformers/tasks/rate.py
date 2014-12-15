import re
import functools

from collections import OrderedDict

from .util import encode_id


def group_by(keys, arr):
    groupped = OrderedDict()
    for item in arr:
        if isinstance(keys, list):
            key = tuple([item[p] for p in keys])
        else:
            key = item[keys]

        try:
            groupped[key].append(item)
        except KeyError:
            groupped[key] = [item]

    return groupped


def pattern_filter(key, pattern, datum):
    return key in datum and datum[key] and pattern.match(datum[key])


def sum_matching(data, matchKey, pattern, valueKey):
    matching_data = filter(
        functools.partial(pattern_filter, matchKey, pattern), data)
    if len(matching_data) > 0:
        denominator = reduce(
            lambda total, d: total + d[valueKey],
            matching_data, 0
        )
    else:
        denominator = None

    return denominator


def compute_for_date(matchingAttribute, valueAttribute, denominatorRe, numeratorRe, entry):
    (start_at, end_at), data = entry

    data_with_values = filter(
        lambda datum: datum.get(valueAttribute, False), data)
    denominator = sum_matching(
        data_with_values, matchingAttribute, denominatorRe, valueAttribute)
    numerator = sum_matching(
        data_with_values, matchingAttribute, numeratorRe, valueAttribute)

    if numerator is None or denominator is None:
        rate = None
    else:
        rate = numerator / denominator if denominator > 0 else None

    return {
        '_id': encode_id(start_at, end_at),
        '_timestamp': start_at,
        '_start_at': start_at,
        '_end_at': end_at,
        'rate': rate,
    }


def compute(data, options):
    groupped = group_by(['_start_at', '_end_at'], data)
    denominatorRe = re.compile(options['denominatorMatcher'])
    numeratorRe = re.compile(options['numeratorMatcher'])

    return map(
        functools.partial(
            compute_for_date,
            options['matchingAttribute'],
            options['valueAttribute'],
            denominatorRe,
            numeratorRe,
        ),
        groupped.items()
    )

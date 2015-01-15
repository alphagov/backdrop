import re

from .util import group_by


def compile_mappings(mappings):
    compiled = {}

    for mapping, patterns in mappings.iteritems():
        compiled[mapping] = map(re.compile, patterns)

    return compiled


def match_mapping(values, mappings):
    for mapping, re_list in mappings.iteritems():
        if all(map(lambda value, re: re.search(value), values, re_list)):
            return mapping

    return None


def map_data(grouped_data, mappings, mapped_attribute, other_mapping, value_attribute):
    mapped_data = {}

    for grouped_values, data in grouped_data.iteritems():
        start_at = grouped_values[0]
        end_at = grouped_values[1]
        mapping_values = grouped_values[2:]

        mapping = match_mapping(mapping_values, mappings) or other_mapping

        if mapping is not None:
            period_mapping_key = (start_at, end_at, mapping)
            summed_value = reduce(
                lambda sum, datum: sum + datum[value_attribute], data, 0)

            if period_mapping_key in mapped_data:
                mapped_data[period_mapping_key][
                    value_attribute] += summed_value
            else:
                mapped_data[period_mapping_key] = {
                    "_start_at": start_at,
                    "_end_at": end_at,
                    mapped_attribute: mapping,
                    value_attribute: summed_value,
                }

    return mapped_data.values()


def compute(data, options):
    grouped = group_by(
        ['_start_at', '_end_at'] + options['mapping-keys'], data)
    compiled_mappings = compile_mappings(options['mappings'])
    mapped_data = map_data(
        grouped, compiled_mappings,
        options['mapped-attribute'],
        options.get('other-mapping', None),
        options['value-attribute'])

    return mapped_data

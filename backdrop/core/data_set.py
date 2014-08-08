from flask import logging
from .records import add_auto_ids, parse_timestamp, validate_record,\
    add_period_keys
from .validation import validate_record_schema
from .nested_merge import nested_merge
from .errors import InvalidSortError
from backdrop.core.response import PeriodGroupedData, PeriodData, \
    GroupedData, SimpleData

import timeutils
import datetime
from itertools import chain

log = logging.getLogger(__name__)

DEFAULT_MAX_AGE_EXPECTED = 2678400


class DataSet(object):
    def __init__(self, storage, config):
        self.storage = storage
        self.config = config

    @property
    def name(self):
        return self.config['name']

    def is_recent_enough(self):
        max_age_expected = self.get_max_age_expected()

        now = timeutils.now()
        last_updated = self.get_last_updated()

        """
        - If `max_age_expected` is None we're saying
        'hey, we're not going to check this'.
        - If `last_updated` is a null value,
        the data-set has never been updated,
        so it doesn't really give us any value to say
        'you should update this thing you've never updated before'
        because we already know that, right?
        """
        if max_age_expected is None or not last_updated:
            return True

        max_age_expected_delta = datetime.timedelta(seconds=max_age_expected)

        return (now - last_updated) < max_age_expected_delta

    def get_max_age_expected(self):
        return self.config.get('max_age_expected',
                               DEFAULT_MAX_AGE_EXPECTED)

    def get_last_updated(self):
        return self.storage.get_last_updated(self.name)

    def get_seconds_out_of_date(self):
        now = timeutils.now()

        if not self.get_last_updated() or self.get_max_age_expected() is None:
            return None
        else:
            last_updated = self.get_last_updated()

        max_age_delta = datetime.timedelta(
            seconds=self.get_max_age_expected()
        )

        return int((
            now - last_updated - max_age_delta
        ).total_seconds())

    def create_if_not_exists(self):
        if not self.storage.data_set_exists(self.name):
            self.storage.create_data_set(self.name, self.config['capped_size'])

    def empty(self):
        return self.storage.empty_data_set(self.name)

    def store(self, records):
        log.info('received {} records'.format(len(records)))

        # Validate schema

        if 'schema' in self.config:
            for record in records:
                validate_record_schema(record, self.config['schema'])
        # add auto-id keys
        records = add_auto_ids(records, self.config.get('auto_ids', None))
        # parse _timestamp
        records = map(parse_timestamp, records)
        # validate
        records = map(validate_record, records)
        # add period data
        records = map(add_period_keys, records)

        for record in records:
            self.storage.save_record(self.name, record)

    def execute_query(self, query):
        results = self.storage.execute_query(self.name, query)

        data = build_data(results, query)

        if query.delta:
            shift = data.amount_to_shift(query.delta)
            if shift != 0:
                return self.execute_query(query.get_shifted_query(shift))

        if query.flatten and query.is_grouped:
            data = flatten_data(data.data(), query)

        return data.data()


def build_data(results, query):
    if not query.is_grouped:
        # TODO: strip internal fields
        return SimpleData(results)

    results = nested_merge(query.group_keys, query.collect, results)
    results = _sort_grouped_results(results, query.sort_by)
    results = _limit_grouped_results(results, query.limit)

    if query.group_by and query.period:
        data = PeriodGroupedData(results, period=query.period)
        if query.start_at and query.end_at:
            data.fill_missing_periods(
                query.start_at, query.end_at, collect=query.collect)
        return data
    elif query.group_by:
        return GroupedData(results)
    elif query.period:
        data = PeriodData(results, period=query.period)
        if query.start_at and query.end_at:
            data.fill_missing_periods(
                query.start_at, query.end_at, collect=query.collect)
        return data
    else:
        raise AssertionError("A query claiming to be a grouped query was not.")


def _sort_grouped_results(results, sort):
    """Sort a grouped set of results
    """
    if not sort:
        return results
    sorters = {
        "ascending": lambda a, b: cmp(a, b),
        "descending": lambda a, b: cmp(b, a)
    }
    sorter = sorters[sort[1]]
    try:
        results.sort(cmp=sorter, key=lambda a: a[sort[0]])
        return results
    except KeyError:
        raise InvalidSortError('Invalid sort key {0}'.format(sort[0]))


def _limit_grouped_results(results, limit):
    """Limit a grouped set of results
    """
    return results[:limit] if limit else results


def flatten_data(data, query):
    """Flatten nested data
    """

    # flatten the key combinations
    keys = list(chain.from_iterable(query.group_keys))

    # get a list of flat children for each record
    flat_children = [_get_flat_children(record, keys) for record in data]
    # and flatten them into one list
    flat_data = list(chain(*flat_children))

    return flat_data


def _get_flat_children(record, keys):
    # the prefix is a string like 'cabinet-office:desktop'
    prefix = ':'.join([record[k] for k in keys if k in record])
    # we no longer need the items that went into the prefix
    record = {k: v for k, v in record.items() if k not in keys}

    # update records with values if they exist
    if 'values' in record:
        values = record.pop('values')
        recs = [_get_updated_dict(record, i) for i in values]
    else:
        recs = [record]

    # get rid of the extraneous count keys
    count_keys = ['_count', '_group_count']
    recs = [{k: v for k, v in r.items() if k not in count_keys} for r in recs]
    # add prefixes where applicable
    recs = [{_add_prefix(k, prefix): v for k, v in r.items()} for r in recs]
    return recs


def _get_updated_dict(current_dict, new_dict):
    result = current_dict.copy()
    result.update(new_dict)
    return result


def _add_prefix(key_name, prefix):
    # we don't prefix keys beginning with '_'
    if prefix and key_name and key_name[0] != '_':
        return prefix + ':' + key_name
    return key_name

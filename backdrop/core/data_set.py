from flask import logging
from .records import add_auto_ids, parse_timestamps, validate_record,\
    add_period_keys, encode_unicode_records
from .validation import validate_record_schema
from .nested_merge import nested_merge, flat_merge
from .errors import InvalidSortError
from backdrop.core.response import (FlatData, GroupedData, PeriodData,
                                    PeriodGroupedData, PeriodFlatData,
                                    SimpleData)

import timeutils
import datetime

log = logging.getLogger(__name__)

DEFAULT_MAX_AGE_EXPECTED = 2678400


class DataSet(object):

    def __init__(self, storage, config):
        self.storage = storage
        self.config = config

        self._last_updated = None

    @property
    def name(self):
        return self.config['name']

    def is_recent_enough(self):
        seconds_out_of_date = self.get_seconds_out_of_date()

        return seconds_out_of_date is None or seconds_out_of_date < 0

    def get_max_age_expected(self):
        return self.config.get('max_age_expected',
                               DEFAULT_MAX_AGE_EXPECTED)

    def get_last_updated(self):
        if self._last_updated is not None:
            return self._last_updated
        else:
            self._last_updated = self.storage.get_last_updated(self.name)
            return self._last_updated

    def get_seconds_out_of_date(self):
        now = timeutils.now()
        max_age_expected = self.get_max_age_expected()
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
            return None

        max_age_delta = datetime.timedelta(seconds=max_age_expected)

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

        records = encode_unicode_records(records)

        # Validate schema
        errors = []
        if 'schema' in self.config:
            for record in records:
                # doesn't change data, no need to return records
                errors += validate_record_schema(record, self.config['schema'])

        # Add auto-id keys
        records, auto_id_errors = add_auto_ids(
            records,
            self.config.get('auto_ids', None))
        errors += auto_id_errors

        # Parse timestamps
        records, timestamp_errors = separate_errors_and_records(
            map(parse_timestamps, records))
        errors += timestamp_errors

        # Custom record validations
        # doesn't change data, no need to return records
        errors += filter(None, map(validate_record, records))

        # Add period data returns no errors so
        # return if we have errors before this point
        if errors:
            return errors
        else:
            # Add period data
            records = map(add_period_keys, records)

            for record in records:
                self.storage.save_record(self.name, record)
            # errors should be empty
            return errors

    def execute_query(self, query):
        results = self.storage.execute_query(self.name, query)

        data = build_data(results, query)

        if query.delta:
            shift = data.amount_to_shift(query.delta)
            if shift != 0:
                return self.execute_query(query.get_shifted_query(shift))

        return data.data()


def build_data(results, query):
    if not query.is_grouped:
        # TODO: strip internal fields
        return SimpleData(results)

    if query.flatten:
        merge_fn = flat_merge
        group_period_presenter = PeriodFlatData
        group_presenter = FlatData
        period_presenter = PeriodFlatData
    else:
        merge_fn = nested_merge
        group_period_presenter = PeriodGroupedData
        group_presenter = GroupedData
        period_presenter = PeriodData

    results = merge_fn(query.group_keys, query.collect, results)
    results = _sort_grouped_results(results, query.sort_by)
    results = _limit_grouped_results(results, query.limit)

    if query.group_by and query.period:
        data = group_period_presenter(results, period=query.period)
        if query.start_at and query.end_at:
            data.fill_missing_periods(
                query.start_at, query.end_at, collect=query.collect, group_by=query.group_by)
        return data
    elif query.group_by:
        return group_presenter(results)
    elif query.period:
        data = period_presenter(results, period=query.period)
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


def separate_errors_and_records(errors_and_records):
    """
    >>> errors_and_records = [({'the_record':'foo'}, "ERROR"),
    ...                       ({'another':'thing'}, None)]
    >>> separate_errors_and_records(errors_and_records)
    ([{'the_record': 'foo'}, {'another': 'thing'}], ['ERROR'])
    """
    records = map(lambda item: item[0],
                  errors_and_records)
    errors = map(lambda item: item[1],
                 filter(lambda item: item[1] is not None,
                        errors_and_records))
    return (records, errors)

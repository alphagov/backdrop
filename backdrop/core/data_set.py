from collections import namedtuple
from flask import logging
from .records import add_auto_ids, parse_timestamp, validate_record, \
    add_period_keys
from .validation import data_set_is_valid
from .nested_merge import nested_merge
from .errors import InvalidSortError
from backdrop.read.response import PeriodGroupedData, PeriodData, \
    GroupedData, SimpleData

import timeutils
import datetime

log = logging.getLogger(__name__)


class NewDataSet(object):
    def __init__(self, storage, config):
        self.storage = storage
        self.config = config

    @property
    def name(self):
        return self.config.name

    def is_recent_enough(self):
        if self.config.max_age_expected is None:
            return True

        max_age_expected = datetime.timedelta(
            seconds=self.config.max_age_expected)

        now = timeutils.now()
        last_updated = self.get_last_updated()

        if not last_updated:
            return False

        return (now - last_updated) < max_age_expected

    def get_last_updated(self):
        return self.storage.get_last_updated(self.config.name)

    def empty(self):
        return self.storage.empty_data_set(self.config.name)

    def store(self, records):
        log.info('received {} records'.format(len(records)))

        # add auto-id keys
        records = add_auto_ids(records, self.config.auto_ids)
        # parse _timestamp
        records = map(parse_timestamp, records)
        # validate
        records = map(validate_record, records)
        # add period data
        records = map(add_period_keys, records)

        for record in records:
            self.storage.save_record(self.config.name, record)

    def execute_query(self, query):
        results = self.storage.execute_query(self.config.name, query)

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


_DataSetConfig = namedtuple(
    "_DataSetConfig",
    "name data_group data_type raw_queries_allowed bearer_token upload_format "
    "upload_filters auto_ids queryable realtime capped_size max_age_expected")


class DataSetConfig(_DataSetConfig):

    def __new__(cls, name, data_group, data_type, raw_queries_allowed=False,
                bearer_token=None, upload_format="csv", upload_filters=None,
                auto_ids=None, queryable=True, realtime=False,
                capped_size=5040, max_age_expected=2678400,
                published=True):
        if not data_set_is_valid(name):
            raise ValueError("DataSet name is not valid: '{}'".format(name))

        if not upload_filters:
            upload_filters = [
                "backdrop.core.upload.filters.first_sheet_filter"]

        return super(DataSetConfig, cls).__new__(cls, name, data_group,
                                                 data_type,
                                                 raw_queries_allowed,
                                                 bearer_token, upload_format,
                                                 upload_filters, auto_ids,
                                                 queryable, realtime,
                                                 capped_size, max_age_expected)

    @property
    def max_age(self):
        """ Set cache-control header length based on type of data_set. """
        return 120 if self.realtime else 1800

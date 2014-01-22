from collections import namedtuple

import pytz
from backdrop.core.timeseries import parse_period
from backdrop.core.timeutils import now, parse_time_as_utc
from backdrop.read.response import *


def if_present(func, value):
    """Apply the given function to the value and return if it exists"""
    if value is not None:
        return func(value)


def parse_request_args(request_args):
    args = dict()

    args['start_at'] = if_present(parse_time_as_utc,
                                  request_args.get('start_at'))

    args['end_at'] = if_present(parse_time_as_utc,
                                request_args.get('end_at'))

    args['delta'] = if_present(int, request_args.get('delta'))

    args['date'] = if_present(parse_time_as_utc,
                              request_args.get('date'))

    args['period'] = if_present(parse_period,
                                request_args.get('period'))

    def boolify(value):
        return {
            "true": True,
            "false": False,
        }.get(value, value)

    def parse_filter_by(filter_by):
        key, value = filter_by.split(':', 1)

        return [key, boolify(value)]

    args['filter_by'] = map(parse_filter_by, request_args.getlist('filter_by'))

    args['group_by'] = request_args.get('group_by')

    args['sort_by'] = if_present(lambda sort_by: sort_by.split(':', 1),
                                 request_args.get('sort_by'))

    args['limit'] = if_present(int, request_args.get('limit'))

    args['collect'] = []
    for collect_arg in request_args.getlist('collect'):
        if ':' in collect_arg:
            args['collect'].append(tuple(collect_arg.split(':')))
        else:
            args['collect'].append((collect_arg, 'default'))

    return args


_Query = namedtuple(
    '_Query',
    ['start_at', 'end_at', 'date', 'delta', 'period',
     'filter_by', 'group_by', 'sort_by', 'limit', 'collect'])


class Query(_Query):
    @classmethod
    def create(cls,
               start_at=None, end_at=None, date=None, delta=None,
               period=None, filter_by=None, group_by=None,
               sort_by=None, limit=None, collect=None):
        if delta is not None:
            start_at, end_at = cls.__calculate_start_and_end(period, date,
                                                             delta)
        return Query(start_at, end_at, date, delta, period,
                     filter_by or [], group_by, sort_by, limit, collect or [])

    @classmethod
    def parse(cls, request_args):
        args = parse_request_args(request_args)
        return Query.create(**args)

    @staticmethod
    def __calculate_start_and_end(period, date, delta):
        date = date or now()

        duration = period.delta * delta

        if delta > 0:
            date = period.end(date)
            start_at = date
            end_at = date + duration
        else:
            date = period.start(date)
            start_at = date + duration
            end_at = date
        return start_at, end_at

    def __skip_blanks(self, data, repository):
        direction = 1

        if self.delta < 0:
            data = tuple(reversed(data))
            direction = -1

        if data[0]['_count'] == 0:
            # we need to skip blank results
            first_nonempty_idx = next(
                (i for i, d in enumerate(data) if d['_count'] > 0),
                None)

            if first_nonempty_idx is None:
                # we currently return no results if none of the
                # results in the specified range contained any data
                data = tuple()
            else:
                query = self.get_shifted_query(first_nonempty_idx * direction)
                data = query.execute(repository)
        return data

    def get_shifted_query(self, shift):
        """Return a new Query where the date is shifted by n periods"""
        new_date = self.date + (self.period.delta * shift)

        args = self._asdict()
        args['date'] = new_date

        return Query.create(**args)

    def to_mongo_query(self):

        mongo_query = {}
        if self.start_at or self.end_at:
            mongo_query["_timestamp"] = {}
            if self.end_at:
                mongo_query["_timestamp"]["$lt"] = self.end_at
            if self.start_at:
                mongo_query["_timestamp"]["$gte"] = self.start_at
        if self.filter_by:
            mongo_query.update(self.filter_by)
        return mongo_query

    def execute(self, repository):
        if self.group_by and self.period:
            data = self.__execute_period_group_query(repository).data()
        elif self.group_by:
            data = self.__execute_grouped_query(repository).data()
        elif self.period:
            data = self.__execute_period_query(repository).data()
        else:
            data = self.__execute_query(repository).data()

        if self.delta is not None:
            data = self.__skip_blanks(data, repository)

        return data

    def __get_period_key(self):
        return self.period.start_at_key

    def __execute_period_group_query(self, repository):
        period_key = self.__get_period_key()

        cursor = repository.multi_group(
            self.group_by, period_key, self,
            sort=self.sort_by, limit=self.limit,
            collect=self.collect
        )

        results = PeriodGroupedData(cursor, period=self.period)

        if self.start_at and self.end_at:
            results.fill_missing_periods(
                self.start_at, self.end_at, collect=self.collect)

        return results

    def __execute_grouped_query(self, repository):
        cursor = repository.group(self.group_by, self, self.sort_by,
                                  self.limit, self.collect)

        results = GroupedData(cursor)
        return results

    def __execute_period_query(self, repository):
        period_key = self.__get_period_key()
        sort = [period_key, "ascending"]
        cursor = repository.group(
            period_key, self,
            sort=sort, limit=self.limit, collect=self.collect
        )

        results = PeriodData(cursor, period=self.period)

        if self.start_at and self.end_at:
            results.fill_missing_periods(
                self.start_at, self.end_at, collect=self.collect)

        return results

    def __execute_query(self, repository):
        cursor = repository.find(
            self, sort=self.sort_by, limit=self.limit)

        results = SimpleData(cursor)
        return results

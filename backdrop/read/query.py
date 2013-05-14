from collections import namedtuple

from dateutil import parser
import pytz
from backdrop.read.response import *


def utc(dt):
    return dt.replace(tzinfo=pytz.UTC)


def parse_time_string(time_string):
    time = parser.parse(time_string)
    return time.astimezone(pytz.utc)


def parse_request_args(request_args):
    args = {}

    if 'start_at' in request_args:
        args['start_at'] = parse_time_string(request_args['start_at'])
    else:
        args['start_at'] = None

    if 'end_at' in request_args:
        args['end_at'] = parse_time_string(request_args['end_at'])
    else:
        args['end_at'] = None

    if 'filter_by' in request_args:
        args['filter_by'] = [
            f.split(':', 1) for f in request_args.getlist('filter_by')
        ]
    else:
        args['filter_by'] = None

    if 'period' in request_args:
        args['period'] = request_args['period']
    else:
        args['period'] = None

    if 'group_by' in request_args:
        args['group_by'] = request_args['group_by']
    else:
        args['group_by'] = None

    if 'sort_by' in request_args:
        args['sort_by'] = request_args['sort_by'].split(':', 1)
    else:
        args['sort_by'] = None

    if 'limit' in request_args:
        args['limit'] = int(request_args['limit'])
    else:
        args['limit'] = None

    args['collect'] = request_args.getlist('collect')
    return args


_Query = namedtuple(
    '_Query',
    'start_at end_at filter_by period group_by sort_by limit collect'
)


class Query(_Query):
    @classmethod
    def create(cls,
               start_at=None, end_at=None, filter_by=None, period=None,
               group_by=None, sort_by=None, limit=None, collect=None):
        return Query(start_at, end_at, filter_by, period,
                     group_by, sort_by, limit, collect or [])

    @classmethod
    def parse(cls, request_args):
        args = parse_request_args(request_args)
        return Query(**args)

    def to_mongo_query(self):
        mongo_query = {}
        if (self.start_at or self.end_at):
            mongo_query["_timestamp"] = {}
            if (self.end_at):
                mongo_query["_timestamp"]["$lt"] = self.end_at
            if (self.start_at):
                mongo_query["_timestamp"]["$gte"] = self.start_at
        if (self.filter_by):
            for filters in self.filter_by:
                if filters[1] == "true":
                    filters[1] = True
                if filters[1] == "false":
                    filters[1] = False
                mongo_query.update({filters[0]: filters[1]})
        return mongo_query

    def execute(self, repository):
        if self.group_by and self.period:
            result = self.__execute_weekly_group_query(repository)
        elif self.group_by:
            result = self.__execute_grouped_query(repository)
        elif self.period:
            result = self.__execute_period_query(repository)
        else:
            result = self.__execute_query(repository)
        return result

    def __execute_weekly_group_query(self, repository):
        period_key = '_week_start_at'

        cursor = repository.multi_group(
            self.group_by, period_key, self,
            sort=self.sort_by, limit=self.limit,
            collect=self.collect
        )

        results = WeeklyGroupedData(cursor)

        if self.start_at and self.end_at:
            results.fill_missing_weeks(self.start_at, self.end_at)

        return results

    def __execute_grouped_query(self, repository):
        cursor = repository.group(self.group_by, self, self.sort_by,
                                  self.limit, self.collect)

        results = GroupedData(cursor)
        return results

    def __execute_period_query(self, repository):
        period_key = '_week_start_at'
        sort = ["_week_start_at", "ascending"]
        cursor = repository.group(
            period_key, self,
            sort=sort, limit=self.limit
        )

        results = PeriodData(cursor)

        if self.start_at and self.end_at:
            results.fill_missing_weeks(self.start_at, self.end_at)

        return results

    def __execute_query(self, repository):
        cursor = repository.find(
            self, sort=self.sort_by, limit=self.limit)

        results = SimpleData(cursor)
        return results

from collections import namedtuple
import datetime

from dateutil import parser
import pytz
from backdrop.core.timeseries import timeseries, WEEK


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

    if 'collect' in request_args:
        args['collect'] = request_args.getlist('collect')
    else:
        args['collect'] = None
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
                     group_by, sort_by, limit, collect)

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
            result = self.execute_period_query(repository)
        else:
            result = self.__execute_query(repository)
        return result

    def _period_group(self, doc):
        start = utc(doc['_week_start_at'])
        return {
            '_start_at': start,
            '_end_at': start + datetime.timedelta(days=7),
            '_count': doc['_count']
        }

    def _ensure_monday(self, week_start_at):
        if week_start_at.weekday() is not 0:
            raise ValueError('Weeks MUST start on Monday. '
                             'Corrupt Data: ' + str(week_start_at))

    def _create_week_timeseries(self, start_at, end_at, results):
        return timeseries(start=start_at,
                          end=end_at,
                          period=WEEK,
                          data=results,
                          default={"_count": 0})

    def __execute_weekly_group_query(self, repository):
        period_key = '_week_start_at'
        result = []

        cursor = repository.multi_group(
            self.group_by, period_key, self,
            sort=self.sort_by, limit=self.limit,
            collect=self.collect or []
        )

        for doc in cursor:
            subgroup = doc.pop('_subgroup')
            [self._ensure_monday(item['_week_start_at']) for item in subgroup]
            doc['values'] = [self._period_group(item) for item in subgroup]

            result.append(doc)

        if self.start_at and self.end_at:
            for i, _ in enumerate(result):
                result[i]['values'] = self._create_week_timeseries(
                    self.start_at, self.end_at, result[i]['values'])

        return result

    def __execute_grouped_query(self, repository):
        return repository.group(self.group_by,
                                self,
                                self.sort_by,
                                self.limit,
                                self.collect or [])

    def execute_period_query(self, repository):
        period_key = '_week_start_at'
        sort = ["_week_start_at", "ascending"]
        cursor = repository.group(
            period_key, self,
            sort=sort, limit=self.limit
        )

        [self._ensure_monday(doc['_week_start_at']) for doc in cursor]
        result = [self._period_group(doc) for doc in cursor]
        if self.start_at and self.end_at:
            result = self._create_week_timeseries(self.start_at,
                                                  self.end_at, result)
        return result

    def __execute_query(self, repository):
        cursor = repository.find(
            self, sort=self.sort_by, limit=self.limit)

        result = []
        for doc in cursor:
            # stringify the id
            doc['_id'] = str(doc['_id'])
            if '_timestamp' in doc:
                doc['_timestamp'] = utc(doc['_timestamp'])
            result.append(doc)
        return result

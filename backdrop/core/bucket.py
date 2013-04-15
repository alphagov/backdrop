import datetime
from dateutil.relativedelta import relativedelta, MO
import pytz
from backdrop.core.timeseries import timeseries, WEEK
from .database import build_query


def utc(dt):
    return dt.replace(tzinfo=pytz.UTC)


class Bucket(object):
    def __init__(self, db, bucket_name):
        self.bucket_name = bucket_name
        self.repository = db.get_repository(bucket_name)

    def store(self, records):
        if isinstance(records, list):
            [self.repository.save(record.to_mongo()) for record in records]
        else:
            self.repository.save(records.to_mongo())

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

    def execute_weekly_group_query(self, group_by, params, sort=None,
                                   limit=None, collect=None):
        period_key = '_week_start_at'
        result = []
        cursor = self.repository.multi_group(
            group_by, period_key, build_query(**params),
            sort=sort, limit=limit,
            collect=collect or []
        )
        for doc in cursor:
            subgroup = doc.pop('_subgroup')
            [self._ensure_monday(item['_week_start_at']) for item in subgroup]
            doc['values'] = [self._period_group(item) for item in subgroup]

            result.append(doc)

        if params.get("start_at") and params.get("end_at"):
            for i, _ in enumerate(result):
                result[i]['values'] = self._create_week_timeseries(
                    params['start_at'], params['end_at'], result[i]['values'])

        return result

    def execute_grouped_query(self, group_by, query,
                              sort=None, limit=None, collect=None):
        return self.repository.group(group_by, query, sort, limit,
                                     collect or [])

    def execute_period_query(self, params, limit=None):
        cursor = self.repository.group(
            '_week_start_at', build_query(**params),
            sort=["_week_start_at", "ascending"], limit=limit)
        [self._ensure_monday(doc['_week_start_at']) for doc in cursor]
        result = [self._period_group(doc) for doc in cursor]
        if params.get("start_at") and params.get("end_at"):
            result = self._create_week_timeseries(params['start_at'],
                                                  params['end_at'], result)
        return result

    def execute_query(self, query, sort=None, limit=None):
        result = []
        cursor = self.repository.find(query, sort=sort, limit=limit)
        for doc in cursor:
            # stringify the id
            doc['_id'] = str(doc['_id'])
            if '_timestamp' in doc:
                doc['_timestamp'] = utc(doc['_timestamp'])
            result.append(doc)
        return result

    def query(self, **params):
        query = build_query(**params)
        sort_by = params.get('sort_by')
        group_by = params.get('group_by')
        limit = params.get('limit')
        collect = params.get('collect')

        if group_by and 'period' in params:
            result = self.execute_weekly_group_query(
                group_by, params, sort_by, limit, collect)
        elif group_by:
            result = self.execute_grouped_query(
                group_by, query, sort_by, limit, collect)
        elif 'period' in params:
            result = self.execute_period_query(params, limit)
        else:
            result = self.execute_query(query, sort_by, limit)

        return result

import datetime

from hamcrest import assert_that, contains, has_entry

from backdrop.core.query import Query
from backdrop.core.timeseries import WEEK
from tests.support.test_helpers import d_tz


class BaseDataSetIntegrationTest(object):

    def setup__timestamp_data(self):
        self._save({
            "_id": 'last',
            "_timestamp": d_tz(2013, 3, 1),
            "_week_start_at": d_tz(2013, 2, 25),
            "_updated_at": d_tz(2013, 8, 10)
        })
        self._save({
            "_id": 'first',
            "_timestamp": d_tz(2013, 1, 1),
            "_week_start_at": d_tz(2012, 12, 31),
            "_updated_at": d_tz(2013, 9, 10)
        })
        self._save({
            "_id": 'second',
            "_timestamp": d_tz(2013, 2, 1),
            "_week_start_at": d_tz(2013, 1, 28),
            "_updated_at": d_tz(2013, 10, 10)
        })

    def test_period_queries_get_sorted_by__week_start_at(self):
        self.setup__timestamp_data()
        query = Query.create(period=WEEK)
        result = self.data_set.execute_query(query)
        assert_that(result, contains(
            has_entry('_start_at', d_tz(2012, 12, 31)),
            has_entry('_start_at', d_tz(2013, 1, 28)),
            has_entry('_start_at', d_tz(2013, 2, 25))
        ))

    def test_data_set_is_recent_enough(self):
        self._save({
            "_id": "first",
            "_updated_at": datetime.datetime.now() - datetime.timedelta(seconds=500)
        })
        assert_that(self.data_set.is_recent_enough())

    def test_data_set_is_not_recent_enough(self):
        self._save({
            "_id": "first",
            "_updated_at": datetime.datetime.now() - datetime.timedelta(seconds=50000)
        })
        assert_that(not self.data_set.is_recent_enough())

    def _save(self, obj):
        raise NotImplemented()

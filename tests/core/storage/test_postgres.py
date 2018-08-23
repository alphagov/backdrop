import unittest
from hamcrest import assert_that, is_
from backdrop.core.storage.postgres import PostgresStorageEngine
from .test_storage import BaseStorageTest
from backdrop.core.query import Query
from backdrop.core.timeseries import DAY, WEEK

def setup_module():
    PostgresStorageEngine('postgres://postgres:mysecretpassword@localhost:5432').create_table_and_indices()

class TestPostgresStorageEngine(BaseStorageTest):
    def setup(self):
        self.engine = PostgresStorageEngine('postgres://postgres:mysecretpassword@localhost:5432')

    def test_get_basic_postgres_query(self):
        result = self.engine._get_basic_postgres_query(
            'some-collection',
            Query.create(filter_by = [('foo', 'bar')])
        )
        assert_that(
            result,
            is_("SELECT record FROM mongo WHERE collection='some-collection' AND record ->> 'foo' = 'bar' LIMIT ALL")
        )

    def test_get_group_by_period_postgres_query(self):
        query = Query.create(period=DAY)
        result = self.engine._get_grouped_postgres_query(
            'some-collection',
            query,
            self.engine._get_groups_lookup(query)
        )
        assert_that(
            result,
            is_("SELECT count(*) as _count, date_trunc('day', timestamp) as _day_start_at FROM mongo GROUP BY _day_start_at")
        )

    def test_get_group_by_record_postgres_query(self):
        query = Query.create(period=WEEK)
        result = self.engine._get_grouped_postgres_query(
            'some-collection',
            query,
            self.engine._get_groups_lookup(query)
        )
        assert_that(
            result,
            is_("SELECT count(*) as _count, date_trunc('week', timestamp) as _week_start_at FROM mongo GROUP BY _week_start_at")
        )

    def test_get_group_by_record_and_period_postgres_query(self):
        query = Query.create(period=WEEK, group_by=['foo'])
        result = self.engine._get_grouped_postgres_query(
            'some-collection',
            query,
            self.engine._get_groups_lookup(query)
        )
        assert_that(
            result,
            is_("SELECT count(*) as _count, date_trunc('week', timestamp) as _week_start_at, record->'foo' as record_0 FROM mongo WHERE record->'foo' IS NOT NULL GROUP BY _week_start_at, record_0")
        )

    @unittest.skip('The postgres datastore does not support the creation of empty datasets')
    def test_create(self):
        pass

    @unittest.skip('The postgres datastore does not support the creation of empty datasets')
    def test_create_fails_if_it_already_exists(self):
        pass

    def test_filter_by_from_query(self):
        result = self.engine._get_where_conditions(Query.create(filter_by = [
            ('foo', 'bar'),
            ('bar', 'baz'),
            ('message', 'hello world')
        ]))
        assert_that(result, is_([
            "record ->> 'foo' = 'bar'",
            "record ->> 'bar' = 'baz'",
            "record ->> 'message' = 'hello world'"
        ]))

    def teardown(self):
        self.engine.delete_data_set('foo_bar')

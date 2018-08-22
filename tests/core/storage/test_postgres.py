import unittest
from hamcrest import assert_that, is_
from backdrop.core.storage.postgres import PostgresStorageEngine
from .test_storage import BaseStorageTest
from backdrop.core.query import Query

def setup_module():
    PostgresStorageEngine('postgres://localhost:5432/backdrop').create_table_and_indices()

class TestPostgresStorageEngine(BaseStorageTest):
    def setup(self):
        self.engine = PostgresStorageEngine('postgres://postgres:mysecretpassword@localhost:5432')

    def test_get_postgres_query(self):
        result = self.engine._get_postgres_query(
            'some-collection',
            Query.create(filter_by = [('foo', 'bar')])
        )
        assert_that(
            result,
            is_("SELECT record FROM mongo WHERE collection='some-collection' AND record ->> 'foo' = 'bar' LIMIT ALL")
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

import unittest
from datetime import datetime

from backdrop.core.storage.postgres import PostgresStorageEngine
from backdrop.core.data_set import DataSet
from backdrop.core.storage.sql_query_factory import create_update_record_query

from .test_data_set_integration import BaseDataSetIntegrationTest

DATABASE_URL = 'postgres://postgres@localhost:5432'
DATA_SET = 'data_set_integration_test'


class TestPostgresDataSetIntegration(BaseDataSetIntegrationTest, unittest.TestCase):
    def setUp(self):
        self.storage = PostgresStorageEngine(DATABASE_URL)

        self.config = {
            'name': DATA_SET,
            'data_group': "group",
            'data_type': "type",
            'max_age_expected': 1000,
        }

        self.data_set = DataSet(self.storage, self.config)

        self.storage.create_table_and_indices()

    def tearDown(self):
        self.storage.empty_data_set(DATA_SET)

    def _save(self, obj):
        updated_at = obj['_updated_at']
        ts = obj['_timestamp'] if '_timestamp' in obj else updated_at
        with self.storage.connection.cursor() as cursor:
            cursor.execute(create_update_record_query(cursor.mogrify, DATA_SET, obj, obj['_id'], ts, updated_at))
            self.storage.connection.commit()

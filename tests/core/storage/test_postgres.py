import unittest

from backdrop.core.storage.postgres import PostgresStorageEngine
from .test_storage import BaseStorageTest


def setup_module():
    PostgresStorageEngine('postgres://postgres@localhost:5432').create_table_and_indices()


class TestPostgresStorageEngine(BaseStorageTest):
    def setup(self):
        self.engine = PostgresStorageEngine('postgres://postgres:mysecretpassword@localhost:5432')

    @unittest.skip('The postgres datastore does not support the creation of empty datasets')
    def test_create(self):
        pass

    @unittest.skip('The postgres datastore does not support the creation of empty datasets')
    def test_create_fails_if_it_already_exists(self):
        pass

    @unittest.skip('The postgres datastore does not support capping dataset sizes')
    def test_capped_data_set_is_capped(self):
        pass

    def teardown(self):
        self.engine.delete_data_set('foo_bar')

from backdrop.core.storage.postgres import PostgresStorageEngine

from .test_storage import BaseStorageTest

class TestPostgresStorageEngine(BaseStorageTest):
    def setup(self):
        self.engine = PostgresStorageEngine('postgres://postgres:mysecretpassword@localhost:5432')

    def teardown(self):
        self.engine.delete_data_set('foo_bar')

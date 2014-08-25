from backdrop.core.storage.postgres import PostgresStorageEngine

from .test_storage import BaseStorageTest

class TestPostgresStorageEngine(BaseStorageTest):
    def setup(self):
        self.engine = PostgresStorageEngine.create(
            "host=localhost dbname=backdrop user=backdrop password=securem8")

    def teardown(self):
        with self.engine._conn.cursor() as cursor:
            sql = "SELECT table_name, table_schema " + \
                  "FROM information_schema.tables " + \
                  "WHERE table_schema NOT LIKE 'pg_%' AND table_schema != 'information_schema'";
            cursor.execute(sql)
            table_names = [row[0] for row in cursor]
        for table_name in table_names:
            self.engine.delete_data_set(table_name)   
        del self.engine


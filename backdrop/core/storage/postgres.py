import psycopg2
import json
from datetime import date, datetime
from .. import timeutils

def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

class PostgresStorageEngine(object):

    def __init__(self, datatbase_url):
        self.connection = psycopg2.connect(datatbase_url)

    def data_set_exists(self, data_set_id):
        # This is slightly different to the mongo implementation
        # in that it will return False if `create_data_set` has
        # been called, but no records have been saved.
        with self.connection.cursor() as psql_cursor:
            psql_cursor.execute("""
                SELECT 1 FROM mongo
                WHERE collection=%(collection)s
                LIMIT 1
                """,
                {'collection': data_set_id}
            )
            return psql_cursor.fetchone() is not None

    def create_data_set(self, data_set_id, size):
        pass

    def delete_data_set(self, data_set_id):
        with self.connection.cursor() as psql_cursor:
            psql_cursor.execute(
                "DELETE FROM mongo WHERE collection=%(collection)s",
                {'collection': data_set_id}
            )
            self.connection.commit()

    def get_last_updated(self, data_set_id):
        # TODO - this requires a bit of sorting on the JSON column
        pass

    def batch_last_updated(self, data_sets):
        # TODO - this requires quite a complex query
        pass

    def empty_data_set(self, data_set_id):
        self.delete_data_set(data_set_id)

    def save_record(self, data_set_id, record):
        self.update_record(data_set_id, record['_id'], record)

    def find_record(self, data_set_id, record_id):
        with self.connection.cursor() as psql_cursor:
            psql_cursor.execute("""
                SELECT record FROM mongo
                WHERE id=%(id)s
                """,
                {'id': record_id}
            )
            (record,) = psql_cursor.fetchone()
            return record

    def update_record(self, data_set_id, record_id, record):
        record['_updated_at'] = timeutils.now()
        record_id = data_set_id + ':' + record_id
        with self.connection.cursor() as psql_cursor:
            psql_cursor.execute("""
                INSERT INTO mongo (id, collection, record)
                VALUES (%(id)s, %(collection)s, %(record)s)
                ON CONFLICT (id) DO UPDATE SET record=%(record)s""",
                {
                    'id': record_id,
                    'collection': data_set_id,
                    'record': json.dumps(record, default=json_serial)
                }

            )
            self.connection.commit()

    def delete_record(self, data_set_id, record_id):
        with self.connection.cursor() as psql_cursor:
            psql_cursor.execute(
                "DELETE FROM mongo WHERE id=%(id)s",
                {'id': record_id}
            )
            self.connection.commit()

    def execute_query(self, data_set_id, query):
        # TODO
        with self.connection.cursor() as psql_cursor:
            psql_cursor.execute("""
                SELECT record FROM mongo
                WHERE collection=%(collection)s
                """,
                {'collection': data_set_id}
            )
            records = psql_cursor.fetchall()
            return [record for (record,) in records]

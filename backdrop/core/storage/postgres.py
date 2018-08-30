from datetime import datetime

import dateutil.parser
import dateutil.tz
import psycopg2
import psycopg2.extras
import pytz

from uuid import uuid4

from sql_query_factory import (
    create_sql_query,
    create_data_set_exists_query,
    create_delete_data_set_query,
    create_get_last_updated_query,
    create_find_record_query,
    create_update_record_query,
    create_delete_record_query,
    create_batch_last_updated_query,
    CREATE_TABLE_SQL,
    DROP_TABLE_SQL,
)
from .. import timeutils


class PostgresStorageEngine(object):

    def __init__(self, datatbase_url):
        self.connection = psycopg2.connect(datatbase_url)

    def create_table_and_indices(self):
        """
        This is probably only going to be used by the tests, or run manually
        when setting up the database for the first time.

        Database migrations are for losers (it is in fact us, the people who
        support this project, who are the losers).
        """
        with self.connection.cursor() as cursor:
            cursor.execute(CREATE_TABLE_SQL)
        self.connection.commit()

    def drop_table_and_indices(self):
        """
        As with the create above, this is likely only used during tests.
        """
        with self.connection.cursor() as cursor:
            cursor.execute(DROP_TABLE_SQL)
        self.connection.commit()

    def data_set_exists(self, data_set_id):
        # This is slightly different to the mongo implementation
        # in that it will return False if `create_data_set` has
        # been called, but no records have been saved.
        with self.connection.cursor() as cursor:
            cursor.execute(
                create_data_set_exists_query(cursor.mogrify, data_set_id))
            return cursor.rowcount > 0

    def create_data_set(self, data_set_id, size):
        pass

    def delete_data_set(self, data_set_id):
        with self.connection.cursor() as cursor:
            cursor.execute(
                create_delete_data_set_query(cursor.mogrify, data_set_id))
            self.connection.commit()

    def get_last_updated(self, data_set_id):
        with self.connection.cursor() as cursor:
            cursor.execute(
                create_get_last_updated_query(cursor.mogrify, data_set_id))

            if cursor.rowcount == 0:
                return None

            (record,) = cursor.fetchone()
            return _parse_datetime_fields(record)['_updated_at']

    def batch_last_updated(self, data_sets):
        collections = [collection.name for collection in data_sets]
        with self.connection.cursor() as cursor:
            cursor.execute(
                create_batch_last_updated_query(cursor.mogrify, collections))
            results = cursor.fetchall()
            timestamp_by_collection = {
                collection: max_timestamp for [collection, max_timestamp] in results}
            for data_set in data_sets:
                if timestamp_by_collection[data_set.name] is not None:
                    data_set._last_updated = timestamp_by_collection[
                        data_set.name].replace(tzinfo=pytz.UTC)
                else:
                    data_set._last_updated = None

    def empty_data_set(self, data_set_id):
        self.delete_data_set(data_set_id)

    def save_record(self, data_set_id, record):

        if '_id' not in record:
            # Mongo used to add an _id field automatically.
            # Postgres doesn't, so we're replicating the functionality here:
            record['_id'] = str(uuid4())

        self.update_record(data_set_id, record['_id'], record)

    def find_record(self, data_set_id, record_id):
        with self.connection.cursor() as cursor:
            cursor.execute(
                create_find_record_query(cursor.mogrify, data_set_id, record_id))
            (record,) = cursor.fetchone()
            return _parse_datetime_fields(record)

    def update_record(self, data_set_id, record_id, record):
        updated_at = timeutils.now()
        record['_updated_at'] = updated_at
        ts = record['_timestamp'] if '_timestamp' in record else updated_at

        with self.connection.cursor() as cursor:
            cursor.execute(create_update_record_query(
                cursor.mogrify, data_set_id, record, record_id, ts, updated_at))
            self.connection.commit()

    def delete_record(self, data_set_id, record_id):
        with self.connection.cursor() as cursor:
            cursor.execute(
                create_delete_record_query(cursor.mogrify, data_set_id, record_id))
            self.connection.commit()

    def execute_query(self, data_set_id, query):
        with self.connection.cursor() as cursor:
            pg_query, convert_query_result_to_dictionaries = create_sql_query(
                cursor.mogrify, data_set_id, query)
            cursor.execute(pg_query)
            records = convert_query_result_to_dictionaries(cursor.fetchall())
            return [_parse_datetime_fields(record) for record in records]


def _parse_datetime_fields(obj):
    """
    The code expects _updated_at to be a datetime, but it's stored as a string.

    >>> _parse_datetime_fields({'_updated_at':'1988-01-20T00:00:00'})
    {'_updated_at': datetime.datetime(1988, 1, 20, 0, 0, tzinfo=<UTC>)}
    """
    obj_copy = obj.copy()
    for field in ['_updated_at', '_timestamp']:
        if field in obj:
            obj_copy[field] = dateutil.parser.parse(
                obj[field]).replace(tzinfo=pytz.UTC)
    for key, value in obj.iteritems():
        if isinstance(value, datetime):
            obj_copy[key] = value.replace(tzinfo=pytz.UTC)
    return obj_copy

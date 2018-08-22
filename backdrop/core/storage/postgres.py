import psycopg2
import json
from datetime import date, datetime
from .. import timeutils
import dateutil.parser

def json_serial(obj):
    """
    Helper to allow python's json.dumps() funtion to handle datetimes.

    >>> json.dumps({'birthday': datetime(1988, 01, 20)}, default=json_serial)
    '{"birthday": "1988-01-20T00:00:00"}'
    """

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def parse_datetime_fields(obj):
    """
    The code expects _updated_at to be a datetime, but it's stored as a string.

    >>> parse_datetime_fields({'_updated_at':'1988-01-20T00:00:00'})
    {'_updated_at': datetime.datetime(1988, 1, 20, 0, 0)}
    """

    cp = obj.copy()
    if '_updated_at' in obj:
        cp['_updated_at'] = dateutil.parser.parse(obj['_updated_at'])
    return cp

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
                {'id': data_set_id + ':' + record_id}
            )
            self.connection.commit()

    def execute_query(self, data_set_id, query):
        with self.connection.cursor() as psql_cursor:
            where_conditions = self._get_where_conditions(query)
            psql_cursor.execute(self._get_postgres_query(data_set_id, query))
            records = psql_cursor.fetchall()
            return [parse_datetime_fields(record) for (record,) in records]

    def _get_postgres_query(self, data_set_id, query):
        with self.connection.cursor() as psql_cursor:
            where_conditions = self._get_where_conditions(query)
            return psql_cursor.mogrify("SELECT record FROM mongo " +
                "WHERE " + " AND ".join(["collection=%(collection)s"] + where_conditions),
                {'collection': data_set_id}
            )

    def _get_where_conditions(self, query):
        """
        Converts a query into a list of conditions to be concatenated into a where query
        """

        if not query or not query.filter_by:
            return []

        with self.connection.cursor() as psql_cursor:
            return [
                psql_cursor.mogrify(
                    "record ->> %(key)s = %(value)s",
                    {'key': tup[0], 'value': tup[1]}
                )
                for tup in query.filter_by
            ]


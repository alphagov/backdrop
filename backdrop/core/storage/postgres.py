import psycopg2
import json
from datetime import date, datetime
from .. import timeutils
import dateutil.parser
import dateutil.tz
import pytz

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
    obj_copy = obj.copy()
    for field in ['_updated_at', '_timestamp']:
        if field in obj:
            obj_copy[field ] = dateutil.parser.parse(obj[field ]).replace(tzinfo=pytz.UTC)
    return obj_copy

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
        with self.connection.cursor() as psql_cursor:
            psql_cursor.execute("""
                CREATE TABLE IF NOT EXISTS mongo (
                    id         VARCHAR   PRIMARY KEY,
                    collection VARCHAR   NOT NULL,
                    timestamp  TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    record     JSON      NOT NULL
                );
                CREATE INDEX IF NOT EXISTS mongo_collection ON mongo (collection);
                CREATE INDEX IF NOT EXISTS mongo_timestamp ON mongo (timestamp);
                CREATE INDEX IF NOT EXISTS mongo_updated_at ON mongo (updated_at);
            """)
        self.connection.commit()

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
        with self.connection.cursor() as psql_cursor:
            psql_cursor.execute("""
                SELECT record FROM mongo
                WHERE collection = %(collection)s
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                {'collection': data_set_id}
            )

            if psql_cursor.rowcount == 0:
                return None

            (record,) = psql_cursor.fetchone()
            return parse_datetime_fields(record)['_updated_at']

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
                {'id': data_set_id + ':' + record_id}
            )
            (record,) = psql_cursor.fetchone()
            return parse_datetime_fields(record)

    def update_record(self, data_set_id, record_id, record):
        updated_at = timeutils.now()
        record['_updated_at'] = updated_at
        ts = record['_timestamp'] if '_timestamp' in record else updated_at

        record_id = data_set_id + ':' + record_id
        with self.connection.cursor() as psql_cursor:
            psql_cursor.execute("""
                INSERT INTO mongo (id, collection, timestamp, updated_at, record)
                VALUES
                (
                    %(id)s,
                    %(collection)s,
                    %(timestamp)s,
                    %(updated_at)s,
                    %(record)s
                )
                ON CONFLICT (id) DO UPDATE SET
                    timestamp=%(timestamp)s,
                    updated_at=%(updated_at)s,
                    record=%(record)s
                """,
                {
                    'id': record_id,
                    'collection': data_set_id,
                    'timestamp': ts,
                    'updated_at': record['_updated_at'],
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
            psql_cursor.execute(self._get_postgres_query(data_set_id, query))
            records = psql_cursor.fetchall()
            return [parse_datetime_fields(record) for (record,) in records]

    def _get_postgres_query(self, data_set_id, query):
        with self.connection.cursor() as psql_cursor:
            where_conditions = self._get_where_conditions(query)
            time_limit_conditions = self._get_time_limit_conditions(query)
            limit = self._get_limit(query)
            sort_by = self._get_sort_by(query)
            return psql_cursor.mogrify(
                " ".join([line for line in [
                    "SELECT record FROM mongo",
                    "WHERE",
                    " AND ".join(
                        ["collection=%(collection)s"] +
                        where_conditions +
                        time_limit_conditions
                    ),
                    sort_by,
                    limit,
                ] if len(line) > 0]),
                {'collection': data_set_id}
            )

    def _get_limit(self, query):
        if not query.limit:
            return 'LIMIT ALL'
        with self.connection.cursor() as psql_cursor:
            return psql_cursor.mogrify('LIMIT %(limit)s', {'limit': query.limit})

    def _get_sort_by(self, query):
        if not query.sort_by:
            return ''

        field, order = query.sort_by
        order = order.upper().replace('ENDING', '')

        if order not in ['ASC', 'DESC']:
            return ''

        with self.connection.cursor() as psql_cursor:
            return psql_cursor.mogrify(
                'ORDER BY record->>%(field)s ' + order,
                {'field': field},
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

    def _get_time_limit_conditions(self, query):
        """
        Converts a query into a list of conditions to be concatenated into a where query
        These conditions are only based on start_at and end_at
        """

        if not query:
            return []

        clauses = []

        if query.start_at:
            with self.connection.cursor() as psql_cursor:
                clauses.append(psql_cursor.mogrify(
                    'timestamp >= %(start_at)s',
                    {'start_at': query.start_at}
                ))

        if query.end_at:
            with self.connection.cursor() as psql_cursor:
                operator = '<=' if query.inclusive else '<'
                clauses.append(psql_cursor.mogrify(
                    'timestamp ' + operator + ' %(end_at)s',
                    {'end_at': query.end_at}
                ))

        return clauses


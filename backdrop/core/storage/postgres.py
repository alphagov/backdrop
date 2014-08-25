import logging
import json
import uuid
import datetime

import psycopg2
from psycopg2.extras import DictCursor

from .. import timeutils
from ..errors import DataSetCreationError

logger = logging.getLogger(__name__)

class JsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return timeutils.as_utc(obj).isoformat()
        return json.JSONEncoder.default(self, obj)

class PostgresStorageEngine(object):
    @classmethod
    def create(cls, conn_str):
        return cls(psycopg2.connect(conn_str))

    def __init__(self, conn):
        self._conn = conn

    def __del__(self):
        self._conn.close()

    def alive(self):
        return self._conn.closed is 0

    def data_set_exists(self, data_set_id):
        with self._conn.cursor() as cursor:
            sql = """
                SELECT EXISTS(
                    SELECT *
                    FROM information_schema.tables
                    WHERE table_name = %s
                );"""
            cursor.execute(sql, (data_set_id, ))
            return cursor.fetchone()[0]

    def create_data_set(self, data_set_id, size, schema):
        try:
            with self._conn.cursor() as cursor:
                if size:
                    self._create_capped(cursor, data_set_id, size, schema)
                else:
                    self._create_uncapped(cursor, data_set_id, schema)
        except psycopg2.ProgrammingError as e:
            self._conn.rollback()
            raise DataSetCreationError(e.message)

    def _create_capped(self, cursor, data_set_id, size, schema):
        create_sequence_sql = """
CREATE SEQUENCE "seq:{}" MAXVALUE {} CYCLE;
""".format(data_set_id, size + 1)
        create_table_sql = """
CREATE TABLE {} (
    id integer PRIMARY KEY,
    updated_at timestamp with time zone not null,
    timestamp timestamp with time zone null,
    data json
);""".format(data_set_id)
        create_save_sql = """
CREATE FUNCTION "save:{0}"(record_id varchar(255), record_updated_at timestamp with time zone, record_timestamp timestamp with time zone, record_data json) RETURNS VOID AS $$
DECLARE
    new_id integer;
BEGIN
    SELECT nextval('seq:{0}') INTO new_id;
    UPDATE {0} SET updated_at = record_updated_at, timestamp = record_timestamp, data = record_data WHERE id = new_id;
    INSERT INTO {0}(id, updated_at, timestamp, data)
        SELECT new_id, record_updated_at, record_timestamp, record_data
        WHERE NOT EXISTS (SELECT 1 FROM {0} WHERE id=new_id);
END
$$ LANGUAGE plpgsql;
""".format(data_set_id)
        cursor.execute(create_sequence_sql)
        cursor.execute(create_table_sql)
        cursor.execute(create_save_sql)

    def _create_uncapped(self, cursor, data_set_id, schema):
        create_table_sql = """
CREATE TABLE {} (
    id varchar(255) PRIMARY KEY,
    updated_at timestamp with time zone NOT NULL,
    timestamp timestamp with time zone NULL,
    data json
);
""".format(data_set_id)
        create_save_sql = """
CREATE FUNCTION "save:{0}"(record_id varchar(255), record_updated_at timestamp with time zone, record_timestamp timestamp with time zone, record_data json)
RETURNS VOID AS $$
DECLARE
    new_id integer;
BEGIN
    UPDATE {0} SET updated_at = record_updated_at, timestamp = record_timestamp, data = record_data WHERE id = record_id;
    INSERT INTO {0}(id, updated_at, timestamp, data)
        SELECT record_id, record_updated_at, record_timestamp, record_data
        WHERE NOT EXISTS (SELECT 1 FROM {0} WHERE id=record_id);
END
$$ LANGUAGE plpgsql;
""".format(data_set_id)
        cursor.execute(create_table_sql)
        cursor.execute(create_save_sql)

    def delete_data_set(self, data_set_id):
        with self._conn.cursor() as cursor:
            # TODO: lol database injection
            cursor.execute("DROP TABLE {};".format(data_set_id))
            cursor.execute('DROP SEQUENCE IF EXISTS "seq:{}";'.format(data_set_id))
            cursor.execute('DROP FUNCTION "save:{}"(record_id varchar(255), record_updated_at timestamp with time zone, record_timestamp timestamp with time zone, record_data json);'.format(data_set_id))

    def get_last_updated(self, data_set_id):
        if not self.data_set_exists(data_set_id):
            return None
        with self._conn.cursor() as cursor:
            # TODO: lol database injection
            sql = "SELECT updated_at " + \
                  "FROM {} " + \
                  "ORDER BY updated_at DESC;"
            cursor.execute(sql.format(data_set_id))
            # TODO: handle error
            return cursor.fetchone()[0]

    def empty_data_set(self, data_set_id):
        with self._conn.cursor() as cursor:
            sql = "DELETE FROM {};".format(data_set_id)
            cursor.execute(sql)

    def save_record(self, data_set_id, record):
        with self._conn.cursor() as cursor:
            cursor.execute(
                'SELECT "save:{}"(%s, %s, %s, %s);'.format(data_set_id),
                (
                    pop(record, '_id', str(uuid.uuid4())),
                    timeutils.now(),
                    pop(record, '_timestamp', None),
                    json.dumps(record, cls=JsonEncoder)
                ))

    def execute_query(self, data_set_id, query):
        if query.is_grouped:
            return self._group_query(data_set_id, query)
        else:
            return self._basic_query(data_set_id, query)

    def _group_query(self, data_set_id, query):
        with self._conn.cursor(cursor_factory=DictCursor) as cursor:
            sql = "SELECT {} FROM {} {} {} LIMIT %s"

    def _basic_query(self, data_set_id, query):
        with self._conn.cursor(cursor_factory=DictCursor) as cursor:
            sql = """
SELECT id, updated_at, timestamp, data
FROM {} {} {}
LIMIT %s"""
            where, values = get_pg_where(query)
            sql = sql.format(
                data_set_id,
                where,
                get_pg_sort(query))
            cursor.execute(sql, values + (query.limit,))

            for row in cursor:
                record = dict(row.items())
                del record['data']
                record = dict(record.items() + row['data'].items())
                record['_id'] = record.pop('id')
                record['_timestamp'] = record.pop('timestamp')
                record['_updated_at'] = record.pop('updated_at')

                yield record

def pop(record, key, default):
    if key in record:
        return record.pop(key)
    else:
        return default

def get_pg_where(query):
    """
    >>> from ...read.query import Query
    >>> from datetime import datetime as dt
    >>> get_pg_where(Query.create())
    ('', ())
    >>> get_pg_where(Query.create(filter_by=[('foo', 'bar')]))
    ("WHERE data->>'foo' = %s", ('bar',))
    >>> get_pg_where(Query.create(start_at=dt(2012, 12, 12, 0, 0)))
    ('WHERE timestamp >= %s', (datetime.datetime(2012, 12, 12, 0, 0),))
    """
    filters = []
    values = []
    if query.filter_by:
        filters += ["data->>'{}' = %s".format(field) for field, _ in query.filter_by]
        values += [value for _, value in query.filter_by]
    if query.start_at:
        filters.append('timestamp >= %s')
        values.append(query.start_at)
    if query.end_at:
        filters.append('timestamp < %s')
        values.append(query.end_at)

    if len(filters) > 0:
        return (
            'WHERE ' + ' AND '.join(filters),
            tuple(values))
    else:
        return ('', tuple())


def get_pg_sort(query):
    """
    >>> from ...read.query import Query
    >>> get_pg_sort(Query.create())
    ''
    >>> get_pg_sort(Query.create(sort_by=['_timestamp', 'ascending']))
    'ORDER BY timestamp ASC'
    >>> get_pg_sort(Query.create(sort_by=['_timestamp', 'descending']))
    'ORDER BY timestamp DESC'
    >>> get_pg_sort(Query.create(sort_by=['foo', 'ascending']))
    "ORDER BY data->>'foo' ASC"
    """
    if query.sort_by:
        return "ORDER BY {} {}".format(
            get_pg_sort_field(query.sort_by[0]),
            get_pg_sort_direction(query.sort_by[1]))
    else:
        return ""

def get_pg_sort_field(field):
    if field == '_timestamp':
        return 'timestamp'
    else:
        return "data->>'{}'".format(field)

def get_pg_sort_direction(direction):
    if direction == 'ascending':
        return 'ASC'
    elif direction == 'descending':
        return 'DESC'
    else:
        raise ValueError('Invalid sort direction {}'.format(direction))

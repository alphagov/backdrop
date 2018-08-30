from collections import OrderedDict
from datetime import date, datetime
import json

from backdrop.core.query import Query
from backdrop.core.timeseries import DAY, WEEK

TABLE_NAME = 'mongo'
CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS mongo (
        id         VARCHAR   PRIMARY KEY,
        collection VARCHAR   NOT NULL,
        timestamp  TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL,
        record     JSONB     NOT NULL
    );
    CREATE INDEX IF NOT EXISTS mongo_collection ON mongo (collection);
    CREATE INDEX IF NOT EXISTS mongo_timestamp ON mongo (timestamp);
    CREATE INDEX IF NOT EXISTS mongo_updated_at ON mongo (updated_at);
    CREATE INDEX IF NOT EXISTS mongo_collection_timestamp ON mongo (collection, timestamp);
    CREATE INDEX IF NOT EXISTS mongo_collection_updated_at ON mongo (collection, updated_at);
"""

DROP_TABLE_SQL = """
    DELETE FROM mongo
"""


def create_data_set_exists_query(mogrify, data_set_id):
    return mogrify(
        """
        SELECT 1 FROM mongo
        WHERE collection=%(collection)s
        LIMIT 1
        """,
        {'collection': data_set_id}
    )


def create_delete_data_set_query(mogrify, data_set_id):
    return mogrify(
        "DELETE FROM mongo WHERE collection=%(collection)s",
        {'collection': data_set_id}
    )


def create_get_last_updated_query(mogrify, data_set_id):
    return mogrify(
        """
        SELECT record FROM mongo
        WHERE collection = %(collection)s
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        {'collection': data_set_id}
    )


def create_find_record_query(mogrify, data_set_id, record_id):
    """
    >>> from tests.support.test_helpers import mock_mogrify
    >>> create_find_record_query(mock_mogrify, 'some-collection', 'some-record')
    "SELECT record FROM mongo WHERE id='some-collection:some-record'"
    """

    return mogrify(
        """
        SELECT record FROM mongo
        WHERE id=%(id)s
        """,
        {'id': _create_id(data_set_id, record_id)}
    )


def create_update_record_query(mogrify, data_set_id, record, record_id, ts, updated_at):
    return mogrify(
        """
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
            'id': _create_id(data_set_id, record_id),
            'collection': data_set_id,
            'timestamp': ts,
            'updated_at': updated_at,
            'record': json.dumps(record, default=_json_serialize_datetimes)
        }
    )


def create_delete_record_query(mogrify, data_set_id, record_id):
    return mogrify(
        "DELETE FROM mongo WHERE id=%(id)s",
        {'id': _create_id(data_set_id, record_id)}
    )


def create_batch_last_updated_query(mogrify, collections):
    """
    Creates an sql query that produces the maximum timestamp for
    each collection

    >>> from tests.support.test_helpers import mock_mogrify
    >>> create_batch_last_updated_query(mock_mogrify, ['some-collection', 'another-collection'])
    "SELECT collection, (SELECT max(timestamp) FROM mongo WHERE collection=c.collection) FROM (SELECT UNNEST(ARRAY['some-collection','another-collection']) AS collection) AS c"
    """
    query_template = """
        SELECT collection,
               (SELECT max(timestamp) FROM mongo WHERE collection=c.collection)
        FROM (SELECT UNNEST(ARRAY[{}]) AS collection) AS c
    """
    return mogrify(
        query_template.format(
            ','.join(['%({})s'.format(collection) for collection in collections])),
        {collection: collection for collection in collections}
    )


def create_sql_query(mogrify, data_set_id, user_query):
    """
    Creates a sql query and a funtion which transforms the output into a list
    of dictionaries with correct field names.

    >>> from tests.support.test_helpers import mock_mogrify
    >>> query, fn = create_sql_query(mock_mogrify, 'some-collection', Query.create())
    >>> query
    "SELECT record FROM mongo WHERE collection='some-collection'"
    >>> fn([({"foo":"bar"},)])
    [{'foo': 'bar'}]

    >>> query, fn = create_sql_query(mock_mogrify, 'some-collection', Query.create(group_by=['foo']))
    >>> query
    "SELECT count(*), record->'foo' FROM mongo WHERE collection='some-collection' AND record->'foo' IS NOT NULL GROUP BY record->'foo'"
    >>> fn([[123, 'some-foo-value'], [456, 'other-foo-value']])
    [{'_count': 123, 'foo': 'some-foo-value'}, {'_count': 456, 'foo': 'other-foo-value'}]
    """

    if user_query.is_grouped:
        return _create_grouped_sql_query(mogrify, data_set_id, user_query)
    else:
        return _create_basic_sql_query(mogrify, data_set_id, user_query)


def _create_grouped_sql_query(mogrify, data_set_id, user_query):
    """
    Create a query for the more complex case where the user has specified a group_by

    >>> from tests.support.test_helpers import mock_mogrify

    >>> query, fn = create_sql_query(mock_mogrify, 'some-collection', Query.create(group_by=['foo']))
    >>> query
    "SELECT count(*), record->'foo' FROM mongo WHERE collection='some-collection' AND record->'foo' IS NOT NULL GROUP BY record->'foo'"
    >>> fn([[123, 'some-foo-value'], [456, 'other-foo-value']])
    [{'_count': 123, 'foo': 'some-foo-value'}, {'_count': 456, 'foo': 'other-foo-value'}]

    >>> query, fn = create_sql_query(mock_mogrify, 'some-collection', Query.create(period=DAY))
    >>> query
    "SELECT count(*), date_trunc('day', timestamp) FROM mongo WHERE collection='some-collection' GROUP BY date_trunc('day', timestamp)"
    >>> fn([[123, '2012-01-01 00:00:00+00:00'], [456, '2012-01-02 00:00:00+00:00']])
    [{'_count': 123, '_day_start_at': '2012-01-01 00:00:00+00:00'}, {'_count': 456, '_day_start_at': '2012-01-02 00:00:00+00:00'}]

    >>> query, fn = create_sql_query(mock_mogrify, 'some-collection', Query.create(group_by=['foo'], period=WEEK))
    >>> query
    "SELECT count(*), date_trunc('week', timestamp), record->'foo' FROM mongo WHERE collection='some-collection' AND record->'foo' IS NOT NULL GROUP BY date_trunc('week', timestamp), record->'foo'"
    >>> fn([[123, '2012-01-01 00:00:00+00:00', 'some-foo-value'], [456, '2012-01-02 00:00:00+00:00', 'another-foo-value']])
    [{'_count': 123, 'foo': 'some-foo-value', '_week_start_at': '2012-01-01 00:00:00+00:00'}, {'_count': 456, 'foo': 'another-foo-value', '_week_start_at': '2012-01-02 00:00:00+00:00'}]

    >>> query, fn = create_sql_query(mock_mogrify, 'some-collection', Query.create(group_by=['foo'], collect=[('bar', 'any-collector')]))
    >>> query
    "SELECT count(*), record->'foo', array_agg(record->'bar') FROM mongo WHERE collection='some-collection' AND record->'foo' IS NOT NULL GROUP BY record->'foo'"
    >>> fn([[123, 'some-foo-value', ['some-bar-value', 'another-bar-value']]])
    [{'_count': 123, 'foo': 'some-foo-value', 'bar': ['some-bar-value', 'another-bar-value']}]
    """

    period_group_by_column_name = _get_period_columns(mogrify, user_query)
    field_group_by_column_name = _get_field_group_columns(mogrify, user_query)
    collect_column_by_column_name = _get_collect_columns(mogrify, user_query)

    group_columns = period_group_by_column_name.values(
    ) + field_group_by_column_name.values()

    columns = (
        ['count(*)'] +
        group_columns +
        collect_column_by_column_name.values()
    )
    where_clauses = (
        [mogrify('collection=%(collection)s', {'collection': data_set_id})] +
        _get_where_conditions(mogrify, user_query) +
        _get_time_limit_conditions(mogrify, user_query) +
        _get_field_group_not_null_conditions(
            field_group_by_column_name.values())
    )
    query_tokens = [
        'SELECT',
        ', '.join([col for col in columns if col]),
        'FROM',
        TABLE_NAME,
        'WHERE',
        ' AND '.join(where_clauses),
        'GROUP BY',
        ', '.join(group_columns)
    ]
    sql_query = ' '.join([token for token in query_tokens if token])

    def translate_results(rows):
        key_by_index = ['_count'] + period_group_by_column_name.keys() + \
            field_group_by_column_name.keys() + \
            collect_column_by_column_name.keys()
        return [_translate_row(row, key_by_index) for row in rows]

    return sql_query, translate_results


def _translate_row(row, key_by_index):
    """
    SQL queries return results as lists of columns. This function translates a
    row into a dictionary of column_name -> value.

    >>> _translate_row([123, 'some-foo-value'], ['_count', 'foo'])
    {'_count': 123, 'foo': 'some-foo-value'}
    """
    return {key_by_index[i]: col for i, col in enumerate(row)}


def _get_field_group_columns(mogrify, user_query):
    return OrderedDict(
        (group, mogrify('record->%(group)s', {'group': group}))
        for group in (user_query.group_by or [])
    )


def _get_field_group_not_null_conditions(field_group_columns):
    return ['%s IS NOT NULL' % field_group_column for field_group_column in (field_group_columns or [])]


def _get_period_columns(mogrify, user_query):
    if user_query.period:
        key = '_{}_start_at'.format(user_query.period.name)
        # There will only ever be one period, so a normal (unordered) dict is
        # fine here
        return {key: mogrify("date_trunc(%(period)s, timestamp)", {'period': user_query.period.name})}
    return {}


def _get_collect_columns(mogrify, user_query):
    return OrderedDict(
        (collect, mogrify(
            "array_agg(record->%(collect)s)", {'collect': collect}))
        for collect, _ in (user_query.collect or [])
    )


def _create_basic_sql_query(mogrify, data_set_id, user_query):
    """
    Create a query for the basic case where the user has not specified a group_by

    >>> from tests.support.test_helpers import mock_mogrify,d_tz
    >>> user_query = Query.create(filter_by=[('foo', 'bar')])
    >>> query, fn = create_sql_query(mock_mogrify, 'some-collection', user_query)
    >>> query
    "SELECT record FROM mongo WHERE collection='some-collection' AND record->>'foo'='bar'"

    >>> user_query = Query.create(filter_by_prefix=[('foo', 'bar')])
    >>> query, fn = create_sql_query(mock_mogrify, 'some-collection', user_query)
    >>> query
    "SELECT record FROM mongo WHERE collection='some-collection' AND record->>'foo' LIKE 'bar%'"

    >>> user_query = Query.create(start_at=d_tz(2012, 12, 12, 13), end_at=d_tz(2013, 1, 1, 13))
    >>> query, fn = create_sql_query(mock_mogrify, 'some-collection', user_query)
    >>> query
    "SELECT record FROM mongo WHERE collection='some-collection' AND timestamp >= '2012-12-12 13:00:00+00:00' AND timestamp < '2013-01-01 13:00:00+00:00'"

    >>> user_query = Query.create(sort_by=('foo', 'ascending'))
    >>> query, fn = create_sql_query(mock_mogrify, 'some-collection', user_query)
    >>> query
    "SELECT record FROM mongo WHERE collection='some-collection' ORDER BY record->>'foo' ASC"

    >>> user_query = Query.create(limit=1)
    >>> query, fn = create_sql_query(mock_mogrify, 'some-collection', user_query)
    >>> query
    "SELECT record FROM mongo WHERE collection='some-collection' LIMIT '1'"
    """

    where_clauses = (
        [mogrify('collection=%(collection)s', {'collection': data_set_id})] +
        _get_where_conditions(mogrify, user_query) +
        _get_time_limit_conditions(mogrify, user_query)
    )
    query_tokens = [
        'SELECT record FROM',
        TABLE_NAME,
        'WHERE',
        ' AND '.join(where_clauses),
        _get_sort_by(mogrify, user_query),
        _get_limit(mogrify, user_query),
    ]
    sql_query = ' '.join([token for token in query_tokens if token])

    return sql_query, lambda rows: [row[0] for row in rows]


def _get_where_conditions(mogrify, user_query):
    filter_by_sql_tokens = [
        mogrify("record->>%(key)s=%(value)s", {'key': key, 'value': value})
        for key, value in (user_query.filter_by or [])
    ]
    filter_by_prefix_sql_tokens = [
        mogrify("record->>%(key)s LIKE %(value)s",
                {'key': key, 'value': '{}%'.format(value)})
        for key, value in (user_query.filter_by_prefix or [])
    ]
    return filter_by_sql_tokens + filter_by_prefix_sql_tokens


def _get_time_limit_conditions(mogrify, user_query):
    """
    Converts a query into a list of conditions to be concatenated into a where query
    These conditions are only based on start_at and end_at
    """
    clauses = []

    if user_query.start_at:
        clauses.append(mogrify(
            'timestamp >= %(start_at)s',
            {'start_at': user_query.start_at}
        ))

    if user_query.end_at:
        operator = '<=' if user_query.inclusive else '<'
        clauses.append(mogrify(
            'timestamp ' + operator + ' %(end_at)s',
            {'end_at': user_query.end_at}
        ))

    return clauses


def _get_sort_by(mogrify, user_query):
    if not user_query.sort_by:
        return None

    field, order = user_query.sort_by
    order = order.upper().replace('ENDING', '')

    if order not in ['ASC', 'DESC']:
        return None

    return mogrify(
        'ORDER BY record->>%(field)s ' + order,
        {'field': field},
    )


def _get_limit(mogrify, user_query):
    return mogrify('LIMIT %(limit)s', {'limit': user_query.limit}) if user_query.limit else None


def _create_id(data_set_id, record_id):
    """
    The record_ids are not necessarily globally unique, because they're user provided and
    are only guaranteed to be unique within a collection. So that we have a unique primary
    key we're joining them with a colon.

    >>> _create_id('foo', 'bar')
    'foo:bar'
    """
    return ':'.join([data_set_id, record_id])


def _json_serialize_datetimes(obj):
    """
    Helper to allow python's json.dumps() funtion to handle datetimes.

    >>> json.dumps({'birthday': datetime(1988, 01, 20)}, default=_json_serialize_datetimes)
    '{"birthday": "1988-01-20T00:00:00"}'
    """

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))

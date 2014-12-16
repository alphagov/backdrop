import os
import logging
import datetime
import itertools

import pymongo
from pymongo.errors import AutoReconnect, CollectionInvalid
from bson import Code

from .. import timeutils
from ..errors import DataSetCreationError


logger = logging.getLogger(__name__)

__all__ = ['MongoStorageEngine']


"""Convert datatime values in a result to UTC

MongoDB ignores offsets, we don't.

>>> convert_datetimes_to_utc({})
{}
>>> convert_datetimes_to_utc({'foo': 'bar'})
{'foo': 'bar'}
>>> convert_datetimes_to_utc({'foo': datetime.datetime(2012, 12, 12)})
{'foo': datetime.datetime(2012, 12, 12, 0, 0, tzinfo=<UTC>)}
"""


def time_as_utc(value):
    if isinstance(value, datetime.datetime):
        return timeutils.as_utc(value)
    return value


def convert_datetimes_to_utc(result):

    return dict((key, time_as_utc(value)) for key, value in result.items())


def get_mongo_client(hosts, port):
    """Return an appropriate mongo client
    """
    client_list = ','.join(':'.join([host, str(port)]) for host in hosts)

    # We can't always guarantee we'll be on 'production'
    # so we allow jenkins to add the set as a variable
    # Some test environments / other envs have their own sets e.g. 'gds-ci'
    replica_set = os.getenv('MONGO_REPLICA_SET', 'production')

    if replica_set == '':
        return pymongo.MongoClient(client_list)
    else:
        return pymongo.MongoReplicaSetClient(
            client_list, replicaSet=replica_set)


def reconnecting_save(collection, record, tries=3):
    """Save to mongo, retrying if necesarry
    """
    try:
        collection.save(record)
    except AutoReconnect:
        logger.warning('AutoReconnect on save : {}'.format(tries))
        if tries > 1:
            return reconnecting_save(collection, record, tries - 1)
        else:
            raise


LAST_UPDATED_COMBINED_JS = """
function(collection_names) {
    return collection_names.map(function(name) {
        return db[name];
    }).filter(function(collection) {
        return collection !== undefined;
    }).map(function(collection, i) {
        query = collection.find().sort({_timestamp:-1}).limit(1);
        return {
            name: collection_names[i],
            last_updated: query.hasNext() ? query.next()['_timestamp'] : undefined
        }
    });
}
"""


class MongoStorageEngine(object):

    @classmethod
    def create(cls, hosts, port, database):
        return cls(get_mongo_client(hosts, port), database)

    def __init__(self, mongo, database):
        self._mongo = mongo
        self._db = mongo[database]

    def _collection(self, data_set_id):
        return self._db[data_set_id]

    def alive(self):
        return self._mongo.alive()

    def data_set_exists(self, data_set_id):
        return data_set_id in self._db.collection_names()

    def create_data_set(self, data_set_id, size):
        try:
            if size > 0:
                self._db.create_collection(data_set_id, capped=True, size=size)
            else:
                self._db.create_collection(data_set_id, capped=False)

            self._collection(data_set_id).create_index(
                [('_timestamp', pymongo.DESCENDING)])
        except CollectionInvalid as e:
            raise DataSetCreationError(e.message)

    def delete_data_set(self, data_set_id):
        self._db.drop_collection(data_set_id)

    def get_last_updated(self, data_set_id):
        last_updated = self._collection(data_set_id).find_one(
            sort=[("_updated_at", pymongo.DESCENDING)])
        if last_updated and last_updated.get('_updated_at') is not None:
            return timeutils.utc(last_updated['_updated_at'])

    def batch_last_updated(self, data_sets):
        all_last_updated = self._db.eval(
            LAST_UPDATED_COMBINED_JS,
            [ds.name for ds in data_sets]
        )

        for i, last_updated in enumerate(all_last_updated):
            data_sets[i]._last_updated = time_as_utc(
                last_updated.get('last_updated', datetime.datetime.min))

    def empty_data_set(self, data_set_id):
        self._collection(data_set_id).remove({})

    def save_record(self, data_set_id, record):
        record['_updated_at'] = timeutils.now()
        self._collection(data_set_id).save(record)

    def execute_query(self, data_set_id, query):
        return map(convert_datetimes_to_utc,
                   self._execute_query(data_set_id, query))

    def _execute_query(self, data_set_id, query):
        if query.is_grouped:
            return self._group_query(data_set_id, query)
        else:
            return self._basic_query(data_set_id, query)

    def _group_query(self, data_set_id, query):
        # flatten the list of key combos to form a flat list of keys
        keys = list(itertools.chain.from_iterable(query.group_keys))
        spec = get_mongo_spec(query)
        collect_fields = query.collect_fields

        return self._collection(data_set_id).group(
            key=keys,
            condition=build_group_condition(keys, spec),
            initial=build_group_initial_state(collect_fields),
            reduce=Code(build_group_reducer(collect_fields)))

    def _basic_query(self, data_set_id, query):
        spec = get_mongo_spec(query)
        sort = get_mongo_sort(query)
        limit = get_mongo_limit(query)

        return self._collection(data_set_id).find(spec, sort=sort, limit=limit)


def get_mongo_spec(query):
    """Convert a Query into a mongo find spec

    PyMongo refers to the query as a spec, this function uses the language
    of the storage engine.

    >>> from ...read.query import Query
    >>> from datetime import datetime as dt
    >>> get_mongo_spec(Query.create())
    {}
    >>> get_mongo_spec(Query.create(filter_by=[('foo', 'bar')]))
    {'foo': 'bar'}
    >>> get_mongo_spec(Query.create(start_at=dt(2012, 12, 12)))
    {'_timestamp': {'$gte': datetime.datetime(2012, 12, 12, 0, 0)}}
    """
    time_range = time_range_to_mongo_query(
        query.start_at, query.end_at, query.inclusive)

    return dict(query.filter_by + time_range.items())


def time_range_to_mongo_query(start_at, end_at, inclusive=False):
    """
    >>> from datetime import datetime as dt
    >>> time_range_to_mongo_query(dt(2012, 12, 12, 12), None)
    {'_timestamp': {'$gte': datetime.datetime(2012, 12, 12, 12, 0)}}
    >>> expected = {'_timestamp': {
    ...  '$gte': dt(2012, 12, 12, 12, 0),
    ...  '$lt': dt(2012, 12, 13, 13, 0)}}
    >>> time_range_to_mongo_query(
    ...   dt(2012, 12, 12, 12), dt(2012, 12, 13, 13)) == expected
    True
    >>> time_range_to_mongo_query(None, None)
    {}
    """
    mongo = {}
    if start_at or end_at:
        mongo['_timestamp'] = {}

        if start_at:
            mongo['_timestamp']['$gte'] = start_at
        if end_at:
            comparator = '$lte' if inclusive else '$lt'
            mongo['_timestamp'][comparator] = end_at

    return mongo


def get_mongo_sort(query):
    """
    >>> from ...read.query import Query
    >>> get_mongo_sort(Query.create())
    >>> get_mongo_sort(Query.create(sort_by=['foo', 'ascending']))
    [('foo', 1)]
    """
    if query.sort_by:
        direction = get_mongo_sort_direction(query.sort_by[1])
        return [(query.sort_by[0], direction)]


def get_mongo_sort_direction(direction):
    """
    >>> get_mongo_sort_direction("invalid")
    >>> get_mongo_sort_direction("ascending")
    1
    >>> get_mongo_sort_direction("descending")
    -1
    """
    return {
        "ascending": pymongo.ASCENDING,
        "descending": pymongo.DESCENDING,
    }.get(direction)


def get_mongo_limit(query):
    """
    >>> from ...read.query import Query
    >>> get_mongo_limit(Query.create())
    0
    >>> get_mongo_limit(Query.create(limit=100))
    100
    """
    return query.limit or 0


def build_group_condition(keys, spec):
    """
    >>> build_group_condition(["foo"], {"bar": "doo"})
    {'foo': {'$ne': None}, 'bar': 'doo'}
    >>> build_group_condition(["foo"], {"foo": "bar"})
    {'foo': 'bar'}
    """
    key_filter = [(key, {'$ne': None}) for key in keys if key not in spec]
    return dict(spec.items() + key_filter)


def build_group_initial_state(collect_fields):
    """
    >>> build_group_initial_state([])
    {'_count': 0}
    >>> build_group_initial_state(["foo"])
    {'_count': 0, 'foo': []}
    """
    initial = {'_count': 0}
    for field in collect_fields:
        initial[field] = []
    return initial


def build_group_reducer(collect_fields):
    template = "function (current, previous)" \
               "{{ previous._count++; {collectors} }}"
    return template.format(
        collectors="\n".join(map(_build_collector_code, collect_fields)))


def _build_collector_code(collect_field):
    template = "if (current['{c}'] !== undefined) " \
               "{{ previous['{c}'].push(current['{c}']); }}"
    return template.format(c=clean_collect_field(collect_field))


def clean_collect_field(collect_field):
    """
    WTF python escaping!?
    >>> clean_collect_field('foo\\\\bar')
    'foo\\\\\\\\bar'
    >>> clean_collect_field("foo'bar")
    "foo\\\\\'bar"
    """
    return collect_field.replace('\\', '\\\\').replace("'", "\\'")

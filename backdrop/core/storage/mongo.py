import datetime
import itertools
import logging
import os
import re

import pymongo
from bson import Code
from pymongo.errors import AutoReconnect, CollectionInvalid

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
    def create(cls, database_url, ca_certificate=None):
        if ca_certificate is not None:
            dir = os.path.dirname(__file__)
            filename = os.path.join(dir, 'mongodb.crt')
            f = open(filename, 'w')
            f.write(ca_certificate)
            f.close()

            mongo_client = pymongo.MongoClient(
                database_url,
                ssl_ca_certs=filename
            )
        else:
            mongo_client = pymongo.MongoClient(database_url)

        return cls(mongo_client)

    def __init__(self, mongo_client):
        self._mongo_client = mongo_client
        self._db = mongo_client.get_database()

    def _collection(self, data_set_id):
        return self._db[data_set_id]

    def alive(self):
        return self._mongo_client.alive()

    # stub methods to maintain API compatibility with postgres
    def create_table_and_indices(self):
        pass

    def drop_table_and_indices(self):
        self._mongo_client.drop_database(
            self._db.name)

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

    def find_record(self, data_set_id, record_id):
        return self._collection(data_set_id).find_one(record_id)

    def update_record(self, data_set_id, record_id, record):
        record['_updated_at'] = timeutils.now()
        self._collection(data_set_id).update(
            {"_id": record_id}, {"$set": record})

    def delete_record(self, data_set_id, record_id):
        self._collection(data_set_id).remove({"_id": record_id})

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
    >>> key, value = get_mongo_spec(Query.create(filter_by_prefix=[['foo', '(bar)']])).items()[0]
    >>> key
    'foo'
    >>> value.pattern
    '^\\\\(bar\\\\).*'
    >>> get_mongo_spec(Query.create(start_at=dt(2012, 12, 12)))
    {'_timestamp': {'$gte': datetime.datetime(2012, 12, 12, 0, 0)}}
    """
    time_range = time_range_to_mongo_query(
        query.start_at, query.end_at, query.inclusive)

    if query.filter_by:
        filter_term = query.filter_by
    else:
        filter_term = [
            [key, _construct_prefix_regex(value)] for key, value in query.filter_by_prefix]

    return dict(filter_term + time_range.items())


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


def _construct_prefix_regex(value):
    return re.compile('^%s.*' % re.escape(value))

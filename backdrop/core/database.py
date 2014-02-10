import logging
import os
from bson import Code
import pymongo
from pymongo.errors import AutoReconnect
from backdrop import statsd
from backdrop.core import timeutils
from backdrop.core.nested_merge import nested_merge, InvalidOperationError


class Database(object):

    def __init__(self, hosts, port, name):
        self._mongo = self.get_client(hosts, port)
        self.name = name

    def get_client(self, hosts, port):
        """
        Create a list to feed to the MongoReplicaSetClient
        e.g. MongoReplicaSetClient(
            [u'hostname_one:27017',
                u'hostname_two:27017',
                    u'hostname_three:27017'])
        See:
        http://bit.ly/1aF3yk3
        http://api.mongodb.org/python/current/examples/high_availability.html
        for more
        """
        client_list = self._client_list(hosts, port)

        # We can't always guarantee we'll be on 'production'
        # so we allow jenkins to add the set as a variable
        # Some test environments / other envs have their own sets e.g. 'gds-ci'
        replica_set = os.getenv('MONGO_REPLICA_SET', 'production')

        if replica_set == '':
            return pymongo.MongoClient(client_list)
        else:
            return pymongo.MongoReplicaSetClient(
                client_list, replicaSet=replica_set)

    def _client_list(self, hosts, port):
        return ','.join('{}:{}'.format(host, port) for host in hosts)

    def alive(self):
        return self._mongo.alive()

    def get_repository(self, bucket_name):
        return Repository(self.get_collection(bucket_name))

    def get_collection(self, collection_name):
        return MongoDriver(self._mongo[self.name][collection_name])

    def collection_names(self):
        return self._mongo[self.name].collection_names()

    def collection_exists(self, collection_name):
        print("{} in? {}".format(collection_name, self.collection_names()))
        return collection_name in self.collection_names()

    def create_uncapped_collection(self, collection_name):
        return self.mongo_database.create_collection(
            name=collection_name, capped=False, size=0)

    def create_capped_collection(self, collection_name, capped_size):
        return self.mongo_database.create_collection(name=collection_name,
                                                     capped=True,
                                                     size=capped_size)

    @property
    def mongo_database(self):
        return self._mongo[self.name]


class MongoDriver(object):

    def __init__(self, collection):
        self._collection = collection
        self.sort_options = {
            "ascending": pymongo.ASCENDING,
            "descending": pymongo.DESCENDING
        }

    def _parse_sort(self, sort):
        if sort:
            key, direction = sort

            if direction not in self.sort_options.keys():
                raise InvalidSortError(direction)

            return [(key, self.sort_options[direction])]

    def find_one(self, query=None, sort=None, limit=0):
        return self._collection.find_one(
            query,
            sort=self._parse_sort(sort),
            limit=limit or 0)

    def find(self, query=None, sort=None, limit=0):
        return self._collection.find(
            query,
            sort=self._parse_sort(sort),
            limit=limit or 0)

    def _ignore_docs_without_grouping_keys(self, keys, query):
        for key in keys:
            if key not in query:
                query[key] = {"$ne": None}
        return query

    def group(self, keys, query, collect_fields):
        return self._collection.group(
            key=keys,
            condition=self._ignore_docs_without_grouping_keys(keys, query),
            initial=self._build_accumulator_initial_state(collect_fields),
            reduce=self._build_reducer_function(collect_fields)
        )

    def _build_collector_code(self, collect_fields):
        template = "if (current['{c}'] !== undefined) " \
                   "{{ previous['{c}'].push(current['{c}']); }}"
        code = [template.format(c=self._clean_collect_field(collect_field))
                for collect_field in collect_fields]
        return "\n".join(code)

    def _clean_collect_field(self, collect_field):
        return collect_field.replace('\\', '\\\\').replace("'", "\\'")

    def _build_accumulator_initial_state(self, collect_fields):
        initial = {'_count': 0}
        for collect_field in collect_fields:
            initial.update({collect_field: []})
        return initial

    def _build_reducer_function(self, collect_fields):
        reducer_skeleton = "function (current, previous)" + \
                           "{{ previous._count++; {collectors} }}"
        reducer_code = reducer_skeleton.format(
            collectors=self._build_collector_code(collect_fields)
        )
        reducer = Code(reducer_code)
        return reducer

    def save(self, obj, tries=3):
        try:
            self._collection.save(obj)
        except AutoReconnect:
            logging.warning("AutoReconnect on save")
            statsd.incr("db.AutoReconnect", bucket=self._collection.name)
            if tries > 1:
                self.save(obj, tries - 1)
            else:
                raise


class Repository(object):

    def __init__(self, mongo_driver):
        self._mongo_driver = mongo_driver

    def _validate_sort(self, sort):
        if len(sort) != 2:
            raise InvalidSortError("Expected a key and direction")

        if sort[1] not in ["ascending", "descending"]:
            raise InvalidSortError(sort[1])

    def find(self, query, sort=None, limit=None):
        if not sort:
            sort = ["_timestamp", "ascending"]

        self._validate_sort(sort)

        is_class = hasattr(query, 'to_mongo_query')
        mongo_query = query.to_mongo_query() if is_class else query

        return self._mongo_driver.find(mongo_query, sort, limit)

    def group(self, group_by, query, sort=None, limit=None, collect=None):
        if sort:
            self._validate_sort(sort)
        return self._group(
            [group_by],
            query.to_mongo_query(),
            sort,
            limit,
            collect or [])

    def save(self, obj):
        obj['_updated_at'] = timeutils.now()
        self._mongo_driver.save(obj)

    def multi_group(self, key1, key2, query,
                    sort=None, limit=None, collect=None):
        if key1 == key2:
            raise GroupingError("Cannot group on two equal keys")
        results = self._group(
            [key1, key2],
            query.to_mongo_query(),
            sort,
            limit,
            collect or [])

        return results

    def _require_keys_in_query(self, keys, query):
        for key in keys:
            if key not in query:
                query[key] = {"$ne": None}
        return query

    def _group(self, keys, query, sort=None, limit=None, collect=None):
        collect_fields = unique_collect_fields(collect)
        results = self._mongo_driver.group(keys, query, list(collect_fields))

        results = nested_merge(keys, collect, results)

        if sort:
            sorters = {
                "ascending": lambda a, b: cmp(a, b),
                "descending": lambda a, b: cmp(b, a)
            }
            sorter = sorters[sort[1]]
            try:
                results.sort(cmp=sorter, key=lambda a: a[sort[0]])
            except KeyError:
                raise InvalidSortError('Invalid sort key {0}'.format(sort[0]))
        if limit:
            results = results[:limit]

        return results


def unique_collect_fields(collect):
    """Return the unique set of field names to collect."""
    return set([collect_field for collect_field, _ in collect])


class GroupingError(ValueError):
    pass


class InvalidSortError(ValueError):
    pass

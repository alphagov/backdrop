from bson import Code
import pymongo


def build_query(**params):
    def ensure_has_timestamp(q):
        if '_timestamp' not in q:
            q['_timestamp'] = {}
        return q

    query = {}
    if 'start_at' in params:
        query = ensure_has_timestamp(query)
        query['_timestamp']['$gte'] = params['start_at']
    if 'end_at' in params:
        query = ensure_has_timestamp(query)
        query['_timestamp']['$lt'] = params['end_at']

    if 'filter_by' in params:
        for key, value in params['filter_by']:
            query[key] = value
    return query


class Database(object):
    def __init__(self, host, port, name):
        self._mongo = pymongo.MongoClient(host, port)
        self.name = name

    def alive(self):
        return self._mongo.alive()

    def get_repository(self, bucket_name):
        return Repository(self._mongo[self.name][bucket_name])

    @property
    def connection(self):
        return self._mongo[self.name]


class Repository(object):
    def __init__(self, collection):
        self._collection = collection

    @property
    def name(self):
        return self._collection.name

    def _validate_sort(self, sort):
        if len(sort) != 2:
            raise InvalidSortError("Expected a key and direction")

        if sort[1] not in ["ascending", "descending"]:
            raise InvalidSortError(sort[1])

    def find(self, query, sort=None, limit=None):
        cursor = self._collection.find(query)
        if sort is not None:
            self._validate_sort(sort)
        else:
            sort = ["_timestamp", "ascending"]
        sort_options = {
            "ascending": pymongo.ASCENDING,
            "descending": pymongo.DESCENDING
        }
        cursor.sort(sort[0], sort_options[sort[1]])
        if limit:
            cursor.limit(limit)

        return cursor

    def group(self, group_by, query, sort=None, limit=None):
        if sort is not None:
            self._validate_sort(sort)
        return self._group([group_by], query, sort, limit)

    def save(self, obj):
        self._collection.save(obj)

    def multi_group(self, key1, key2, query, sort=None, limit=None):
        if key1 == key2:
            raise GroupingError("Cannot group on two equal keys")
        results = self._group([key1, key2], query, sort, limit)

        return results

    def _group(self, keys, query, sort=None, limit=None):
        results = self._collection.group(
            key=keys,
            condition=query,
            initial={'_count': 0},
            reduce=Code("""
                function(current, previous) { previous._count++; }
                """)
        )
        for result in results:
            for key in keys:
                if result[key] is None:
                    return []

        results = nested_merge(keys, results)

        if sort is not None:
            sorters = {
                "ascending": lambda a, b: cmp(a, b),
                "descending": lambda a, b: cmp(b, a)
            }
            sorter = sorters[sort[1]]
            try:
                results.sort(cmp=sorter, key=lambda a: a[sort[0]])
            except KeyError:
                raise InvalidSortError('Invalid sort key {0}'.format(sort[0]))
        if limit is not None:
            results = results[:limit]

        return results


class GroupingError(ValueError):
    pass


class InvalidSortError(ValueError):
    pass


def nested_merge(keys, results):
    output = []
    for result in results:
        output = _merge(output, keys, result)
    return output


def _merge(output, keys, result):
    if len(keys) == 0:
        return output
    value = result.pop(keys[0])
    try:
        item = next(item for item in output if item[keys[0]] == value)
    except StopIteration:
        if len(keys) == 1:
            # we are a leaf
            item = result
            item[keys[0]] = value
        else:
            # we are not a leaf
            item = {
                keys[0]: value,
                "_subgroup": []
            }
        output.append(item)
    if len(keys) > 1:
        # we are not a leaf
        item['_subgroup'] = _merge(item['_subgroup'], keys[1:], result)
        item['_subgroup'].sort(key=lambda d: d[keys[1]])
        item["_count"] = sum(doc.get('_count', 0) for doc in item['_subgroup'])
        item["_group_count"] = len(item['_subgroup'])
    return output

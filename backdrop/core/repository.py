from itertools import groupby
from bson import Code


def build_query(**params):
    query = {}
    if 'start_at' in params:
        query['_timestamp'] = {
            '$gte': params['start_at']
        }
    if 'end_at' in params:
        if '_timestamp' not in query:
            query['_timestamp'] = {}
        query['_timestamp']['$lt'] = params['end_at']

    if 'filter_by' in params:
        for key, value in params['filter_by']:
            query[key] = value
    return query


class Repository(object):
    def __init__(self, collection):
        self._collection = collection

    def find(self, query):
        return self._collection.find(query).sort('_timestamp', -1)

    def group(self, group_by, query):
        return self._collection.group(
            key=[group_by],
            condition=query,
            initial={'count': 0},
            reduce=Code("""
                function(current, previous) { previous.count++; }
                """)
        )

    def save(self, obj):
        self._collection.save(obj)

    def multi_group(self, key1, key2, query):
        results = self._collection.group(
            key=[key1, key2],
            condition=query,
            initial={'count': 0},
            reduce=Code("""
                function(current, previous) { previous.count++; }
                """)
        )

        outer_key = key1
        inner_key = key2

        nested_grouping = []

        grouped_by_outer_value = groupby(sorted(
            results, key=lambda row: row[outer_key]),
            lambda row: row[outer_key])

        for outer_value, outer_groups in grouped_by_outer_value:
            outer_group = {key2: {}}
            outer_group[key1] = outer_value

            inner_group = groupby(sorted(
                outer_groups, key=lambda row: row[inner_key]),
                lambda row: row[inner_key])
            for inner_value, inner_grouping in inner_group:
                outer_group[key2][inner_value] = {"count": 0}
                for elements in inner_grouping:
                    outer_group[key2][inner_value]["count"]\
                        += elements["count"]

            nested_grouping.append(outer_group)

        return nested_grouping

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

    def multi_group(self, group_by_these, query):
        if len(group_by_these) != 2:
            raise Exception("Require two fields to group by, but was: %s" % group_by_these)

        results = self._collection.group(
            key=group_by_these,
            condition=query,
            initial={'count': 0},
            reduce=Code("""
                function(current, previous) { previous.count++; }
                """)
        )

        outer_key = group_by_these[0]
        inner_key = group_by_these[1]
        map = []

        grouped_by_outer_value = groupby(sorted(results, key=lambda row: row[outer_key]),
                    lambda row: row[outer_key])

        for outer_value, outer_groups in grouped_by_outer_value:
            outer_group = {outer_value: {}}

            inner_group = groupby(sorted(outer_groups, key=lambda row: row[inner_key]),
                lambda row: row[inner_key])
            for inner_value, inner_grouping in inner_group:
                outer_group[outer_value][inner_value] = {"count": 0}
                for elements in inner_grouping:
                    outer_group[outer_value][inner_value]["count"] += elements["count"]

            map.append(outer_group)

        return map

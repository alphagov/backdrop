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

    def all(self):
        return self._collection.find()

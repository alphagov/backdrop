from bson import Code


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

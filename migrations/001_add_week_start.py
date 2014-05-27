"""
Add _week_start_at field to all documents in all collections
"""
import logging

from backdrop.core.records import Record
from backdrop.core.timeutils import utc

log = logging.getLogger(__name__)


def up(db):
    # THIS MIGRATION IS NOT COMPATIBLE WITH STORAGE ENGINES
    return None
    for name in db.collection_names():
        log.info("Migrating collection: {0}".format(name))
        collection = db.get_repository(name)
        query = {
            "_timestamp": {"$exists": True},
            "_week_start_at": {"$exists": False}
        }
        for document in collection.find(query):
            document['_timestamp'] = utc(document['_timestamp'])
            record = Record(document)

            collection.save(record.to_mongo())

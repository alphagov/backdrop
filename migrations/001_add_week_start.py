"""
Add _week_start_at field to all documents in all collections
"""
from backdrop.core.storage import utc
from backdrop.core.records import Record
import logging

log = logging.getLogger(__name__)


def up(db):
    for name in db.collection_names():
        log.info("Migrating collection: {0}".format(name))
        collection = db[name]
        query = {
            "_timestamp": {"$exists": True},
            "_week_start_at": {"$exists": False}
        }
        for document in collection.find(query):
            document['_timestamp'] = utc(document['_timestamp'])
            record = Record(document)

            collection.save(record.to_mongo())

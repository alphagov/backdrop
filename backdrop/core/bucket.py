from flask import logging
import backdrop

log = logging.getLogger(__name__)


class Bucket(object):
    def __init__(self, db, bucket_name):
        self.bucket_name = bucket_name
        self.repository = db.get_repository(bucket_name)

    def parse_and_store(self, data):
        log.info("request contains %s documents" % len(data))

        self.store(backdrop.core.records.parse_all(data))

    def store(self, records):
        if isinstance(records, list):
            [self.repository.save(record.to_mongo()) for record in records]
        else:
            self.repository.save(records.to_mongo())

    def query(self, query):
        result = query.execute(self.repository)

        return result

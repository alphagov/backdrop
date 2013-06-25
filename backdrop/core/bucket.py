from base64 import b64encode
from flask import logging
from backdrop.core import records
from backdrop.core.errors import ValidationError

log = logging.getLogger(__name__)


class Bucket(object):
    def __init__(self, db, bucket_name, generate_id_from=None):
        self.bucket_name = bucket_name
        self.repository = db.get_repository(bucket_name)
        self.auto_id_keys = generate_id_from

    def parse_and_store(self, data):
        log.info("request contains %s documents" % len(data))

        if self.auto_id_keys:
            data = [self._add_id(d) for d in data]

        self.store(records.parse_all(data))

    def store(self, records):
        if isinstance(records, list):
            [self.repository.save(record.to_mongo()) for record in records]
        else:
            self.repository.save(records.to_mongo())

    def query(self, query):
        result = query.execute(self.repository)

        return result

    def _add_id(self, datum):
        self._validate_presence_of_auto_id_keys(datum)
        return dict(datum.items() + [("_id", self._generate_id(datum))])

    def _validate_presence_of_auto_id_keys(self, datum):
        if not set(self.auto_id_keys).issubset(set(datum.keys())):
            raise ValidationError(
                "One or more of the following required values is missing: "
                "%s" % ", ".join(self.auto_id_keys))

    def _generate_id(self, datum):
        return b64encode(".".join([datum[key] for key in self.auto_id_keys]))

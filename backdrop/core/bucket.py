from base64 import b64encode
from collections import namedtuple
from flask import logging
from backdrop.core import records
from backdrop.core.errors import ValidationError
from backdrop.core.validation import bucket_is_valid

log = logging.getLogger(__name__)


class Bucket(object):
    def __init__(self, db, config):
        self.bucket_name = config.name
        self.repository = db.get_repository(config.name)
        self.auto_id_keys = config.auto_ids

    def parse_and_store(self, data):
        log.info("received %s documents" % len(data))

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


_BucketConfig = namedtuple(
    "_BucketConfig",
    "name data_group data_type raw_queries_allowed bearer_token upload_format "
    "upload_filters auto_ids queryable realtime capped_size")


class BucketConfig(_BucketConfig):
    def __new__(cls, name, data_group, data_type, raw_queries_allowed=False,
                bearer_token=None, upload_format="csv", upload_filters=None,
                auto_ids=None, queryable=True, realtime=False,
                capped_size=5040):
        if not bucket_is_valid(name):
            raise ValueError("Bucket name is not valid")

        if upload_filters is None:
            upload_filters = [
                "backdrop.core.upload.filters.first_sheet_filter"]

        return super(BucketConfig, cls).__new__(cls, name, data_group,
                                                data_type,
                                                raw_queries_allowed,
                                                bearer_token, upload_format,
                                                upload_filters, auto_ids,
                                                queryable, realtime,
                                                capped_size)

    @property
    def max_age(self):
        return 120 if self.realtime else 1800

from base64 import b64encode
from collections import namedtuple
from flask import logging
from backdrop.core import records
from backdrop.core.errors import ValidationError
from backdrop.core.validation import bucket_is_valid

import timeutils
import datetime

log = logging.getLogger(__name__)


class Bucket(object):

    def __init__(self, db, config):
        self.bucket_name = config.name
        self.repository = db.get_repository(config.name)
        self.auto_id_keys = config.auto_ids
        self.config = config
        self.db = db

    def is_recent_enough(self):
        max_age_expected = datetime.timedelta(
            seconds=self.config.max_age_expected)
        now = timeutils.now()
        last_updated = self.get_last_updated()

        if not last_updated:
            return False

        return (now - last_updated) < max_age_expected

    def get_last_updated(self):
        last_updated = self.db.get_collection(self.config.name).find().sort(
            "_updated_at", -1).limit(1)

        last_updated = last_updated[0].get('_updated_at')

        if last_updated is not None:
            return timeutils.utc(last_updated)

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
    "upload_filters auto_ids queryable realtime capped_size max_age_expected")


class BucketConfig(_BucketConfig):

    def __new__(cls, name, data_group, data_type, raw_queries_allowed=False,
                bearer_token=None, upload_format="csv", upload_filters=None,
                auto_ids=None, queryable=True, realtime=False,
                capped_size=5040, max_age_expected=2678400):
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
                                                capped_size, max_age_expected)

    @property
    def max_age(self):
        """ Set cache-control header length based on type of bucket. """
        return 120 if self.realtime else 1800

"""
Convert Google Analytics data_sets from Europe/London to UTC
"""
import logging
import copy
from itertools import imap, ifilter
from datetime import timedelta

from backdrop.core.records import Record
from backdrop.core.timeutils import utc


log = logging.getLogger(__name__)

GA_DATA_SETS_TO_MIGRATE = [
    "carers_allowance_journey",
    "deposit_foreign_marriage_journey",
    "pay_foreign_marriage_certificates_journey",
    "pay_legalisation_drop_off_journey",
    "pay_legalisation_post_journey",
    "pay_register_birth_abroad_journey",
    "pay_register_death_abroad_journey",
    "lpa_journey",
    "licensing_journey",
]


def fix_timestamp(document):
    """Return a new dict with the _timestamp field fixed
    """
    document = copy.deepcopy(document)
    document['_timestamp'] = document['_timestamp'].replace(tzinfo=None) + \
        timedelta(hours=1)
    return document


def strip_internal_fields(document):
    """Return a new dict with all internal fields removed

    Leaves _timestamp and _id in place
    """
    def allowed_field(key):
        return not key.startswith('_') or key in ['_timestamp', '_id']

    return dict(
        (key, value) for key, value in document.items() if allowed_field(key))


def is_bst(document):
    """Return true if a document looks like it's BST"""
    return document['_timestamp'].hour == 23


def create_record(document):
    """Return a dict with internal fields applied"""
    return Record(document).to_mongo()


def fix_id(document):
    """Return a new dict with the _id field recalculated"""
    def _format(timestamp):
        return to_utc(timestamp).strftime("%Y%m%d%H%M%S")

    def data_id(data_type, timestamp, period):
        """_id generation function copied from backdrop-ga-collector"""
        return base64.urlsafe_b64encode("_".join(
            [data_type, _format(timestamp), period]))

    document = copy.deepcopy(document)
    document['_id'] = data_id(
        document['dataType'], document['_timestamp'],
        document['timeSpan'])

    return document


def up(db):
    # Depracated with the introducetion of MongoStorageEngine
    return None
    for name in GA_DATA_SETS_TO_MIGRATE:
        collection = db.get_repository(name)

        documents = collection.find({})

        documents = ifilter(is_bst, documents)
        documents = imap(strip_internal_fields, documents)
        documents = imap(fix_timestamp, documents)
        documents = map(create_record, documents)

        if len(documents) > 0:
            log.info("Convert GA timezone: {0}".format(name))

        map(collection.save, documents)

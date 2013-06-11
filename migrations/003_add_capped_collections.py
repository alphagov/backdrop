"""
Add capped collections for real time data
"""
import logging

log = logging.getLogger(__name__)


def up(db):
    capped_collections = [
        "govuk_realtime",
        "licensing_realtime"
    ]

    for collection_name in capped_collections:
        db.create_collection(name=collection_name, capped=True, size=5040)
        log.info("created capped collection: %s" % collection_name)

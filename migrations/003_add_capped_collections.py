"""
Add capped collections for real time data
"""
import logging

log = logging.getLogger(__name__)


def up(db):
    capped_collections = [
        "fco-realtime-pay-legalisation-post",
        "fco-realtime-pay-legalisation-drop-off",
        "fco-realtime-pay-register-birth-abroad",
        "fco-realtime-pay-register-death-abroad",
        "fco-realtime-pay-foreign-marriage-certificates",
        "fco-realtime-deposit-foreign-marriage",
        "govuk-realtime",
        "licensing-realtime"
    ]

    for collection_name in capped_collections:
        db.create_collection(name=collection_name, capped=True, size=5040)
        log.info("created capped collection: %s" % collection_name)

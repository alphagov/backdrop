"""
Add capped collections for real time data
"""
import logging

log = logging.getLogger(__name__)


def up(db):
    capped_collections = [
        "fco_pay_legalisation_post_realtime",
        "fco_pay_legalisation_drop_off_realtime",
        "fco_pay_register_birth_abroad_realtime",
        "fco_pay_register_death_abroad_realtime",
        "fco_pay_foreign_marriage_certificates_realtime",
        "fco_deposit_foreign_marriage_realtime",
        "govuk_realtime",
        "licensing_realtime",
    ]

    existing_collections = db.collection_names()

    for collection_name in capped_collections:
        if not collection_name in existing_collections:
            db.create_collection(name=collection_name, capped=True, size=5040)
            log.info("created capped collection: %s" % collection_name)

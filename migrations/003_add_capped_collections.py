"""
Add capped collections for real time data
"""
import logging

log = logging.getLogger(__name__)


def up(db):
    capped_collections = [
        "fco_realtime_pay_legalisation_post",
        "fco_realtime_pay_legalisation_drop_off",
        "fco_realtime_pay_register_birth_abroad",
        "fco_realtime_pay_register_death_abroad",
        "fco_realtime_pay_foreign_marriage_certificates",
        "fco_realtime_deposit_foreign_marriage",
        "govuk_realtime",
        "licensing_realtime",
   ]

    for collection_name in capped_collections:
        db.create_collection(name=collection_name, capped=True, size=5040)
        log.info("created capped collection: %s" % collection_name)

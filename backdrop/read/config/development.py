DATABASE_NAME = "backdrop"
MONGO_HOSTS = ['localhost']
MONGO_PORT = 27017
LOG_LEVEL = "DEBUG"
RAW_QUERIES_ALLOWED = {
    "government_annotations": True,
    "govuk_realtime": True,
    "licence_finder_monitoring": True,
    "licensing": False,
    "licensing_journey": True,
    "licensing_monitoring": True,
    "licensing_realtime": True,
    "lpa_volumes": True,
    "lpa_monitoring": True,
    # electronic vehicle licensing
    "electronic_vehicle_licensing_monitoring": True,
    "evl_customer_satisfaction": True,
    "evl_volumetrics": True,
    "sorn_monitoring": True,
    "sorn_realtime": True,
    "tax_disc_monitoring": True,
    "tax_disc_realtime": True,
    # fco
    "deposit_foreign_marriage_journey": True,
    "deposit_foreign_marriage_monitoring": True,
    "deposit_foreign_marriage_realtime": True,
    "pay_foreign_marriage_certificates_journey": True,
    "pay_foreign_marriage_certificates_monitoring": True,
    "pay_foreign_marriage_certificates_realtime": True,
    "pay_legalisation_drop_off_journey": True,
    "pay_legalisation_drop_off_monitoring": True,
    "pay_legalisation_drop_off_realtime": True,
    "pay_legalisation_post_journey": True,
    "pay_legalisation_post_monitoring": True,
    "pay_legalisation_post_realtime": True,
    "pay_register_birth_abroad_journey": True,
    "pay_register_birth_abroad_monitoring": True,
    "pay_register_birth_abroad_realtime": True,
    "pay_register_death_abroad_journey": True,
    "pay_register_death_abroad_monitoring": True,
    "pay_register_death_abroad_realtime": True,
    # HMRC preview
    "hmrc_preview": True,
    # LPA / Lasting Power of Attorney
    "lpa_journey": True,
}

#STAGECRAFT_URL = 'http://stagecraft.perfplat.dev:3204'
STAGECRAFT_URL = 'http://localhost:8080'
STAGECRAFT_DATA_SET_QUERY_TOKEN = 'stagecraft-data-set-query-token-fake'

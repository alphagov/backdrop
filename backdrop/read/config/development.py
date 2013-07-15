DATABASE_NAME = "backdrop"
MONGO_HOST = 'localhost'
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
}

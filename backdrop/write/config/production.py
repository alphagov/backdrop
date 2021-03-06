import os
from ...core.config.common import load_paas_settings

PAAS = load_paas_settings()
DATABASE_URL = PAAS.get('DATABASE_URL')
DATABASE_ENGINE = PAAS.get('DATABASE_ENGINE')
CA_CERTIFICATE = PAAS.get('CA_CERTIFICATE')
STAGECRAFT_URL = os.getenv('STAGECRAFT_URL')
BROKER_URL = PAAS.get('REDIS_URL') or os.getenv('REDIS_URL')
BROKER_FAILOVER_STRATEGY = "round-robin"
SIGNON_API_USER_TOKEN = os.getenv('SIGNON_API_USER_TOKEN')
LOG_LEVEL = os.getenv("LOG_LEVEL", "ERROR")
DATA_SET_UPLOAD_FORMAT = {
    "ithc_excel": "excel",
}
DATA_SET_UPLOAD_FILTERS = {
    "ithc_excel": [
        "backdrop.core.upload.filters.first_sheet_filter",
    ],
}
SESSION_COOKIE_SECURE = True
SECRET_KEY = os.getenv('SECRET_KEY')
STAGECRAFT_COLLECTION_ENDPOINT_TOKEN = os.getenv(
    'STAGECRAFT_COLLECTION_ENDPOINT_TOKEN')

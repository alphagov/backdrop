import os
from ...core.config.common import load_paas_settings

PAAS = load_paas_settings()
DATABASE_URL = PAAS.get('DATABASE_URL')
STAGECRAFT_URL = os.getenv('STAGECRAFT_URL')
SIGNON_API_USER_TOKEN = os.getenv('SIGNON_API_USER_TOKEN')
LOG_LEVEL = "INFO"
SESSION_COOKIE_SECURE=True

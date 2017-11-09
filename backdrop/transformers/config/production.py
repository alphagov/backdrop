import os
from ...core.config.common import load_paas_settings

PAAS = load_paas_settings()
BROKER_URL = PAAS.get('REDIS_URL') or os.getenv('REDIS_URL')
BROKER_FAILOVER_STRATEGY = "round-robin"
STAGECRAFT_URL = 'https://performance-platform-stagecraft-production.cloudapps.digital'
STAGECRAFT_OAUTH_TOKEN = os.getenv('STAGECRAFT_OAUTH_TOKEN')
BACKDROP_READ_URL = 'https://performance-platform-backdrop-read-production.cloudapps.digital'
BACKDROP_WRITE_URL = 'https://performance-platform-backdrop-write-production.cloudapps.digital'

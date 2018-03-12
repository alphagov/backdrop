DATABASE_URL = 'mongodb://localhost:27017/backdrop_development'
LOG_LEVEL = "DEBUG"
DATA_SET_AUTO_ID_KEYS = {
    "lpa_volumes": ("key", "start_at", "end_at")
}

STAGECRAFT_COLLECTION_ENDPOINT_TOKEN = 'dev-create-endpoint-token'
DEFAULT_COLLECTION = 'default'

try:
    from development_environment import *
except ImportError:
    from development_environment_sample import *

STAGECRAFT_URL = 'http://localhost:3103'

SIGNON_API_USER_TOKEN = 'development-oauth-access-token'

BROKER_URL = 'amqp://backdrop_write:backdrop_write@localhost:5672/%2Fbackdrop_write'

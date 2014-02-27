DATABASE_NAME = "backdrop"
MONGO_HOSTS = ['localhost']
MONGO_PORT = 27017
LOG_LEVEL = "DEBUG"
BUCKET_AUTO_ID_KEYS = {
    "lpa_volumes": ("key", "start_at", "end_at")
}

CREATE_COLLECTION_ENDPOINT_TOKEN = 'dev-create-endpoint-token'

try:
    from development_environment import *
except ImportError:
    from development_environment_sample import *

#STAGECRAFT_URL = 'http://stagecraft.perfplat.dev:3204'
STAGECRAFT_URL = 'http://localhost:8080'
STAGECRAFT_DATA_SET_QUERY_TOKEN = 'stagecraft-data-set-query-token-fake'

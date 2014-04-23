DATABASE_NAME = "backdrop_test"
MONGO_HOSTS = ['localhost']
MONGO_PORT = 27017
LOG_LEVEL = "DEBUG"
CLIENT_ID = "it's not important here"
CLIENT_SECRET = "it's not important here"
DATA_SET_AUTO_ID_KEYS = {
    "data_set_with_auto_id": ["key", "start_at", "end_at"],
    "data_set_with_timestamp_auto_id": ["_timestamp", "key"],
    "evl_volumetrics": ["_timestamp", "service", "transaction"],
}

from development import (CREATE_COLLECTION_ENDPOINT_TOKEN, STAGECRAFT_URL,
                         STAGECRAFT_DATA_SET_QUERY_TOKEN)
from test_environment import *

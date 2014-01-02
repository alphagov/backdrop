DATABASE_NAME = "backdrop_test"
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
LOG_LEVEL = "DEBUG"
CLIENT_ID = "it's not important here"
CLIENT_SECRET = "it's not important here"
BUCKET_AUTO_ID_KEYS = {
    "bucket_with_auto_id": ["key", "start_at", "end_at"],
    "bucket_with_timestamp_auto_id": ["_timestamp", "key"],
    "evl_volumetrics": ["_timestamp", "service", "transaction"],
}

from test_environment import *

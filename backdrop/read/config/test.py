DATABASE_NAME = "backdrop_test"
MONGO_HOSTS = ['localhost']
MONGO_PORT = 27017
LOG_LEVEL = "ERROR"
RAW_QUERIES_ALLOWED = {
    "reptiles": True,
    "foo": True,
    "licensing": True,
    "lizards": True,
    "rawr": True,
    "month": True,
}

from development import STAGECRAFT_URL, STAGECRAFT_DATA_SET_QUERY_TOKEN

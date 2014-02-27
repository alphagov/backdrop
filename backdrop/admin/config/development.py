LOG_LEVEL = "DEBUG"
BACKDROP_ADMIN_UI_HOST = "http://backdrop-admin.dev.gov.uk"
ALLOW_TEST_SIGNIN=True
SECRET_KEY = "something unique and secret"

DATABASE_NAME = "backdrop"
MONGO_HOSTS = ['localhost']
MONGO_PORT = 27017

try:
    from development_environment import *
except ImportError:
    from development_environment_sample import *

STAGECRAFT_URL = 'http://localhost:8080'
STAGECRAFT_DATA_SET_QUERY_TOKEN = 'stagecraft-data-set-query-token-fake'

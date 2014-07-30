import os

LOG_LEVEL = "DEBUG"
BACKDROP_ADMIN_UI_HOST = "http://admin.development.performance.service.gov.uk"
ALLOW_TEST_SIGNIN = True
SECRET_KEY = "something unique and secret"

wercker_mongo_host = os.environ.get('WERCKER_MONGODB_HOST')

DATABASE_NAME = "backdrop"
MONGO_HOSTS = [wercker_mongo_host if wercker_mongo_host else 'localhost']
MONGO_PORT = 27017

import pprint as pp
pp.pprint('<<<<<<<<<<<<<<<<< DEVELOPMENT >>>>>>>>>>>>>>>>>>>>>')
pp.pprint(os.environ.get('WERCKER_MONGODB_HOST'))
pp.pprint(wercker_mongo_host)
pp.pprint(MONGO_HOSTS)

try:
    from development_environment import *
except ImportError:
    from development_environment_sample import *

STAGECRAFT_URL = 'http://localhost:3204'
BACKDROP_URL = 'http://localhost:3039'
STAGECRAFT_DATA_SET_QUERY_TOKEN = 'dev-data-set-query-token'

SIGNON_API_USER_TOKEN = 'development-oauth-access-token'

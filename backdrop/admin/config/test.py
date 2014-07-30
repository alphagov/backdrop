import os

LOG_LEVEL = "DEBUG"
SINGLE_SIGN_ON = True
BACKDROP_ADMIN_UI_HOST = "http://backdrop-admin.dev.gov.uk"
ALLOW_TEST_SIGNIN = True
SECRET_KEY = "something unique and secret"

wercker_mongo_host = os.environ.get('WERCKER_MONGODB_HOST')

DATABASE_NAME = "backdrop_test"

MONGO_HOSTS = [wercker_mongo_host if wercker_mongo_host else 'localhost']
import pprint as pp
pp.pprint(os.environ.get('WERCKER_MONGODB_HOST'))
pp.pprint(wercker_mongo_host)
pp.pprint(MONGO_HOSTS)
MONGO_PORT = 27017

from test_environment import *

from development import (STAGECRAFT_URL, STAGECRAFT_DATA_SET_QUERY_TOKEN,
                         BACKDROP_URL, SIGNON_API_USER_TOKEN)

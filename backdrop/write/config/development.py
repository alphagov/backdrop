DATABASE_NAME = "backdrop"
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
LOG_LEVEL = "DEBUG"
SINGLE_SIGN_ON = True
SECRET_KEY = "something unique and secret"

try:
    from development_environment import *
except ImportError:
    from development_environment_sample import *

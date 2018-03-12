DATABASE_URL = 'mongodb://localhost:27017/backdrop_development'
LOG_LEVEL = "DEBUG"

STAGECRAFT_URL = 'http://localhost:3103'

SIGNON_API_USER_TOKEN = 'development-oauth-access-token'
DEFAULT_COLLECTION = 'default'

try:
    from .development_environment import *
except ImportError:
    pass

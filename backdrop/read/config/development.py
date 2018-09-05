DATABASE_URL = 'postgres://postgres@localhost:5432'
DATABASE_ENGINE = 'postgres'
LOG_LEVEL = "DEBUG"

STAGECRAFT_URL = 'http://localhost:3103'

SIGNON_API_USER_TOKEN = 'development-oauth-access-token'

try:
    from .development_environment import *
except ImportError:
    pass

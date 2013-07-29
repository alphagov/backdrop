DATABASE_NAME = "backdrop_test"
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
SINGLE_SIGN_ON = True
SECRET_KEY = "something unique and secret"
BACKDROP_ADMIN_UI_HOST = "http://backdrop-admin.dev.gov.uk"
LOG_LEVEL = "DEBUG"
CLIENT_ID = "it's not important here"
CLIENT_SECRET = "it's not important here"
ALLOW_TEST_SIGNIN = True
BUCKET_AUTO_ID_KEYS = {
    "bucket_with_auto_id": ("key", "start_at", "end_at")
}
BUCKET_UPLOAD_FORMAT = {
    "my_xlsx_bucket": "excel"
}


from test_environment import *

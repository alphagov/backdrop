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
    "my_xlsx_bucket": "excel",
    "evl_ceg_data": "excel",
    "evl_services_volumetrics": "excel",
    "evl_services_failures": "excel"
}
BUCKET_UPLOAD_FILTERS = {
    "evl_ceg_data": [
        "backdrop.core.upload.filters.first_sheet_filter",
        "backdrop.contrib.evl_upload.ceg_volumes"
    ],
    "evl_services_volumetrics": [
        "backdrop.core.upload.filters.first_sheet_filter",
        "backdrop.contrib.evl_upload.service_volumetrics"
    ],
    "evl_services_failures": [
        "backdrop.contrib.evl_upload.service_failures"
    ]
}


from test_environment import *

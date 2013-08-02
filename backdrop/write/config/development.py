DATABASE_NAME = "backdrop"
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
LOG_LEVEL = "DEBUG"
SINGLE_SIGN_ON = True
SECRET_KEY = "something unique and secret"
BACKDROP_ADMIN_UI_HOST = "http://backdrop-admin.dev.gov.uk"
BUCKET_AUTO_ID_KEYS = {
    "lpa_volumes": ("key", "start_at", "end_at")
}
BUCKET_UPLOAD_FORMAT = {
    "my_xlsx_bucket": "excel",
    "evl_services_volumetrics": "excel"
}
BUCKET_UPLOAD_FILTERS = {
    "evl_ceg_data": [
        "backdrop.contrib.evl_upload.ceg_volumes"
    ],
    "evl_services_volumetrics": [
        "backdrop.contrib.evl_upload.service_volumetrics"
    ]
}
try:
    from development_environment import *
except ImportError:
    from development_environment_sample import *

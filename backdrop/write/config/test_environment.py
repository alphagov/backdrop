TOKENS = {
    '_bucket': '_bucket-bearer-token',
    '_status': '_status-bearer-token',  # not expected to be here
    'bucket': 'bucket-bearer-token',
    'data_with_times': 'data_with_times-bearer-token',
    'flavour_events': 'flavour_events-bearer-token',
    'foo': 'foo-bearer-token',
    'foo_bucket': 'foo_bucket-bearer-token',
    'licensing': 'licensing-bearer-token',
    'my_dinosaur_bucket': 'my_dinosaur_bucket-bearer-token',
    'reptiles': 'reptiles-bearer-token',
    'month': 'month-bearer-token',
    'month_no_raw_access': 'month_no_raw_access-bearer-token'
}
PERMISSIONS = {
    'test@example.com': [
        'my_bucket', 'bucket_with_auto_id', 'foo',
        'my_xlsx_bucket', 'evl_ceg_data', 'evl_services_volumetrics',
        'evl_services_failures', 'evl_channel_volumetrics',
        'evl_customer_satisfaction', 'bucket_with_timestamp_auto_id'
    ],
    'some.other@example.com': ['foo']
}
OAUTH_CLIENT_ID = "it's not important here"
OAUTH_CLIENT_SECRET = "it's not important here"
OAUTH_BASE_URL = "http://signon.dev.gov.uk"

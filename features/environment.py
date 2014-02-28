import logging
import os
import sys
from backdrop.core.log_handler import get_log_file_handler
from features.support.splinter_client import SplinterClient

from features.support.stagecraft import StagecraftService

sys.path.append(
    os.path.join(os.path.dirname(__file__), '..')
)

os.environ["GOVUK_ENV"] = "test"

from support.http_test_client import HTTPTestClient
from support.flask_test_client import FlaskTestClient
from backdrop.read import api as read_api
from backdrop.write import api as write_api
# pick one for test configuration, if they don't match things will fail
from backdrop.write.config import test as config


handler = logging.FileHandler('log/behave.log')
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s - %(name)s - %(filename)s:%(lineno)d] "
    "-> %(message)s"))


log = logging.getLogger()
log.addHandler(handler)

def before_all(context):
    bucket_names = [
            "reptiles", 
            "my_bucket", 
            "foo", 
            "bucket_with_auto_id", 
            "my_xlsx_bucket", 
            "bucket_with_timestamp_auto_id",
            "evl_ceg_data",
            "evl_services_volumetrics",
            "evl_services_failures",
            "evl_channel_volumetrics",
            "evl_customer_satisfaction",
            "evl_volumetrics",
            "flavour_events",
            "day",
            "hour",
            "month",
            "month_with_wrong_timestamp",
            "some_bucket",
            "licensing",
            "my_dinosaur_bucket",
            "data_set_with_times",
            "new-dataset"
        ]
    url_response_dict = {}
    for bucket_name in bucket_names:
        url_response_dict[('GET', 'data-sets/' + bucket_name)] = {
            'bearer_token': "%s-bearer-token" % bucket_name,
            'capped_size': None,
            'name': bucket_name,
            'data_type': bucket_name,
            'realtime': False,
            'auto_ids': '',
            'max_age_expected': 86400,
            'data_group': bucket_name,
            'upload_filters': '',
            'queryable': True,
            'upload_format': '',
            'raw_queries_allowed': True,
        }
    context.mock_stagecraft_server = StagecraftService(8080, url_response_dict)
    context.mock_stagecraft_server.start()


def after_all(context):
    if server_running(context):
        context.mock_stagecraft_server.stop()


def before_feature(context, feature):
    context.client = create_client(feature)


def before_scenario(context, _):
    context.client.before_scenario()
    storage = context.client.storage()
    storage.connection.drop_database(storage.name)
    context.after_handlers = []


def after_scenario(context, scenario):
    context.client.after_scenario(scenario)
    for handler in context.after_handlers:
        try:
            handler()
        except Exception as e:
            log.exception(e)


def server_running(context):
    return 'mock_stagecraft_server' in context and context.mock_stagecraft_server and context.mock_stagecraft_server.running


def after_feature(context, _):
    context.client.spin_down()


def create_client(feature):
    if 'use_read_api_client' in feature.tags:
        return FlaskTestClient(read_api)
    if 'use_write_api_client' in feature.tags:
        return FlaskTestClient(write_api)
    if 'use_http_client' in feature.tags:
        return HTTPTestClient(config.DATABASE_NAME)
    if 'use_admin_client' in feature.tags:
        if os.environ.get('SKIP_SPLINTER_TESTS'):
            class DummyClient(object):
                def spin_down(self):
                    pass
            return DummyClient()

        return SplinterClient(config.DATABASE_NAME, 'admin', '5002')

    raise AssertionError(
        "Test client not selected! Please annotate the failing feature with "
        + "either @use_read_api_client, @use_write_api_client "
        + "or @use_http_client.")

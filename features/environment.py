import test_helper
import os

from support.http_test_client import HTTPTestClient
from support.flask_test_client import FlaskTestClient
from read import api as read_api
from write import api as write_api


DATABASE_NAME = "performance_platform_test"

os.environ["FLASK_ENV"] = "test"


def before_feature(context, feature):
    context.client = init_client(feature)


def before_scenario(context, _):
    storage = context.client.storage()
    name = storage.name
    storage.connection.drop_database(name)


def after_feature(context, _):
    context.client.spin_down()


def init_client(feature):
    if 'use_read_api_client' in feature.tags:
        return FlaskTestClient(read_api, DATABASE_NAME)
    if 'use_write_api_client' in feature.tags:
        return FlaskTestClient(write_api, DATABASE_NAME)
    if 'use_http_client' in feature.tags:
        return HTTPTestClient(DATABASE_NAME)

    raise AssertionError(
        "Test client not selected! Please annotate the failing feature with "
        + "either @use_read_api_client, @use_write_api_client "
        + "or @use_http_client.")

import test_helper
import os

os.environ["GOVUK_ENV"] = "test"

from support.http_test_client import HTTPTestClient
from support.flask_test_client import FlaskTestClient
from backdrop.read import api as read_api
from backdrop.write import api as write_api
# pick one for test configuration, if they don't match things will fail
from backdrop.write.config import test as config


def before_feature(context, feature):
    context.client = create_client(feature)


def before_scenario(context, _):
    storage = context.client.storage()
    name = storage.name
    storage.connection.drop_database(name)


def after_feature(context, _):
    context.client.spin_down()


def create_client(feature):
    if 'use_read_api_client' in feature.tags:
        return FlaskTestClient(read_api)
    if 'use_write_api_client' in feature.tags:
        return FlaskTestClient(write_api)
    if 'use_http_client' in feature.tags:
        return HTTPTestClient(config.DATABASE_NAME)

    raise AssertionError(
        "Test client not selected! Please annotate the failing feature with "
        + "either @use_read_api_client, @use_write_api_client "
        + "or @use_http_client.")

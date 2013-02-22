import test_helper
from performance_platform.read import api as read_api
from performance_platform.write import api as write_api

DATABASE_NAME = "performance_platform_test"


def before_feature(context, feature):
    api = None
    if feature.name == "the performance platform read api":
        api = read_api
    if feature.name == "the performance platform write api":
        api = write_api

    context.database_name = DATABASE_NAME
    api.app.config['DATABASE_NAME'] = DATABASE_NAME
    context.api = api.app.test_client()
    context.mongo = api.mongo[context.database_name]


def after_scenario(context, _):
    if "bucket" in context:
        context.mongo[context.bucket].drop()

import test_helper
from performance_platform.read import api

DATABASE_NAME = "performance_platform_test"


def before_all(context):
    context.database_name = DATABASE_NAME
    api.app.config['DATABASE_NAME'] = DATABASE_NAME
    context.api = api.app.test_client()
    context.mongo = api.mongo[context.database_name]


def after_scenario(context, _):
    api.mongo[DATABASE_NAME][context.bucket].drop()
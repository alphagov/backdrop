import test_helper
from read import api as read_api
from write import api as write_api

DATABASE_NAME = "performance_platform_test"


def before_feature(context, feature):
    api = None
    if feature.name == "the performance platform read api":
        api = read_api
    if feature.name == "the performance platform write api":
        api = write_api

    context.client = FlaskTestClient(api, DATABASE_NAME)


def after_scenario(context, _):
    if "bucket" in context:
        context.client.storage()[context.bucket].drop()


class FlaskTestClient(object):
    def __init__(self, flask_app, database_name):
        flask_app.app.config['DATABASE_NAME'] = database_name
        self._client = flask_app.app.test_client()
        self._storage = flask_app.mongo[database_name]

    def get(self, url):
        return self._client.get(url)

    def post(self, url, **message):
        return self._client.post(url, **message)

    def storage(self):
        return self._storage
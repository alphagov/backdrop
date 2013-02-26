import subprocess
from pymongo import MongoClient
import test_helper
from read import api as read_api
from write import api as write_api
import requests
import time

DATABASE_NAME = "performance_platform_test"


def before_feature(context, feature):
    client_to_use = None
    if feature.name == "the performance platform read api":
        client_to_use = FlaskTestClient(read_api, DATABASE_NAME)
    if feature.name == "the performance platform write api":
        client_to_use = FlaskTestClient(write_api, DATABASE_NAME)
    if feature.name == "end-to-end platform test":
        client_to_use = HTTPTestClient("performance_platform")

    context.client = client_to_use


def after_scenario(context, _):
    if "bucket" in context:
        context.client.storage()[context.bucket].drop()


def after_feature(context, feature):
    context.client.spin_down()


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

    def spin_down(self):
        pass


class HTTPTestResponse:
    def __init__(self, response):
        self.status_code = response.status_code
        self.data = response.text


class HTTPTestClient(object):
    def __init__(self, database_name):
        self.database_name = database_name
        self.read = subprocess.Popen(
            ["python", "performance_platform/start.py", "read"]
        )
        self.write = subprocess.Popen(
            ["python", "performance_platform/start.py", "write"]
        )
        time.sleep(1)  # wait until processes have started

    def get(self, url):
        response = requests.get(self.read_url(url))
        return HTTPTestResponse(response)

    def post(self, url, **message):
        response = requests.post(
            self.write_url(url),
            data=message['data'],
            headers={"Content-type": message['content_type']}
        )
        return HTTPTestResponse(response)

    def storage(self):
        return MongoClient('localhost', 27017)[self.database_name]

    def spin_down(self):
        self.read.kill()
        self.write.kill()

    def read_url(self, url):
        return "http://localhost:5000" + url

    def write_url(self, url):
        return "http://localhost:5001" + url

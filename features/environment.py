import subprocess
from pymongo import MongoClient
import test_helper
from read import api as read_api
from write import api as write_api
import requests
import time
import os

DATABASE_NAME = "performance_platform_test"

os.environ["FLASK_ENV"] = "test"


def before_feature(context, feature):
    client_to_use = None
    if 'use_read_api_client' in feature.tags:
        client_to_use = FlaskTestClient(read_api, DATABASE_NAME)
    if 'use_write_api_client' in feature.tags:
        client_to_use = FlaskTestClient(write_api, DATABASE_NAME)
    if 'use_http_client' in feature.tags:
        client_to_use = HTTPTestClient(DATABASE_NAME)

    context.client = client_to_use


def before_scenario(context, _):
    storage = context.client.storage()
    name = storage.name
    storage.connection.drop_database(name)


def after_feature(context, _):
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
        self.read = self.run_api("read")
        self.write = self.run_api("write")
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
        os.killpg(self.read.pid, 9)
        os.killpg(self.write.pid, 9)

    def run_api(self, api):
        return subprocess.Popen(
            ["python", "performance_platform/start.py", api],
            preexec_fn=os.setsid,
        )

    def read_url(self, url):
        return "http://localhost:5000" + url

    def write_url(self, url):
        return "http://localhost:5001" + url

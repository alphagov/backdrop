import os
import subprocess
import time
from pymongo import MongoClient
import requests


class HTTPTestClient(object):
    def __init__(self, database_name):
        self.database_name = database_name
        self._read_api = Api.start("read", "5000")
        self._write_api = Api.start("write", "5001")

    def get(self, url, headers=None):
        response = requests.get(self._read_api.url(url), headers=headers)
        return HTTPTestResponse(response)

    def post(self, url, **message):
        headers = dict(message.get("headers", []))
        if "data" in message:
            headers.update({"Content-type": message['content_type']})
            response = requests.post(
                self._write_api.url(url),
                data=message['data'],
                headers=headers
            )
        elif "files" in message:
            response = requests.post(
                self._write_api.url(url),
                files=message['files'],
                headers=headers,
            )
        else:
            raise Exception("Incorrect message")
        return HTTPTestResponse(response)

    def storage(self):
        return MongoClient('localhost', 27017)[self.database_name]

    def before_scenario(self):
        pass

    def after_scenario(self):
        pass

    def spin_down(self):
        self._read_api.stop()
        self._write_api.stop()


class HTTPTestResponse:
    def __init__(self, response):
        self.status_code = response.status_code
        self.data = response.text
        self.headers = response.headers


class Api(object):
    @classmethod
    def start(cls, api, port):
        api = Api(api, port)
        api._start()
        return api

    def __init__(self, api, port):
        self._api = api
        self._port = port

    def _start(self):
        self._process = subprocess.Popen(
            ["python", "start.py", self._api, self._port],
            preexec_fn=os.setsid,
            stderr=subprocess.STDOUT, stdout=subprocess.PIPE
        )
        time.sleep(0.3)  # wait until process has started

    def stop(self):
        os.killpg(self._process.pid, 9)

    def url(self, path):
        return 'http://localhost:{0}{1}'.format(self._port, path)



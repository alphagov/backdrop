import os
import subprocess
import time
from pymongo import MongoClient
import requests


class HTTPTestClient(object):
    APP_PORTS = {
        'read': '5000',
        'write': '5001',
    }

    def __init__(self, database_name):
        self.database_name = database_name
        self.read = self.run_api("read")
        self.write = self.run_api("write")
        time.sleep(1)  # wait until processes have started

    def get(self, url, headers=None):
        response = requests.get(self.read_url(url), headers=headers)
        return HTTPTestResponse(response)

    def post(self, url, **message):
        headers = dict(message.get("headers", []))
        if "data" in message:
            headers.update({"Content-type": message['content_type']})
            response = requests.post(
                self.write_url(url),
                data=message['data'],
                headers=headers
            )
        elif "files" in message:
            response = requests.post(
                self.write_url(url),
                files=message['files'],
                headers=headers,
            )
        else:
            raise Exception("Incorrect message")
        return HTTPTestResponse(response)

    def storage(self):
        return MongoClient('localhost', 27017)[self.database_name]

    def spin_down(self):
        os.killpg(self.read.pid, 9)
        os.killpg(self.write.pid, 9)

    def run_api(self, api):
        return subprocess.Popen(
            ["python", "start.py", api, self.APP_PORTS[api]],
            preexec_fn=os.setsid,
        )

    def read_url(self, url):
        return 'http://localhost:{0}{1}'.format(self.APP_PORTS['read'], url)

    def write_url(self, url):
        return 'http://localhost:{0}{1}'.format(self.APP_PORTS['write'], url)


class HTTPTestResponse:
    def __init__(self, response):
        self.status_code = response.status_code
        self.data = response.text
        self.headers = response.headers

import os
import subprocess
import time
from pymongo import MongoClient
import requests


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
            ["python", "start.py", api],
            preexec_fn=os.setsid,
        )

    def read_url(self, url):
        return "http://localhost:5000" + url

    def write_url(self, url):
        return "http://localhost:5001" + url


class HTTPTestResponse:
    def __init__(self, response):
        self.status_code = response.status_code
        self.data = response.text
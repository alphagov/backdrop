from pymongo import MongoClient
import requests
from features.support.support import Api, BaseClient


class HTTPTestClient(BaseClient):
    def __init__(self, database_name):
        self.database_name = database_name
        self._read_api = Api("read", "5000")
        self._write_api = Api("write", "5001")
        self._start()

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
                headers=headers,
                timeout=60,
            )
        elif "files" in message:
            response = requests.post(
                self._write_api.url(url),
                files=message['files'],
                headers=headers,
                timeout=60,
            )
        else:
            raise Exception("Incorrect message")
        return HTTPTestResponse(response)

    def storage(self):
        return MongoClient('localhost', 27017)[self.database_name]

    def spin_down(self):
        self._read_api.stop()
        self._write_api.stop()

    def _start(self):
        try:
            self._read_api.start()
            self._write_api.start()
        except:
            self.spin_down()
            raise


class HTTPTestResponse:
    def __init__(self, response):
        self.status_code = response.status_code
        self.data = response.text
        self.headers = response.headers

from pymongo import MongoClient
import requests

from .support import FlaskApp, BaseClient


class HTTPTestClient(BaseClient):
    def __init__(self, database_url):
        self._read_api = FlaskApp("read", "5000")
        self._write_api = FlaskApp("write", "5001")
        self._mongo_db = MongoClient(database_url).get_database()
        self._start()

    def get(self, url, headers=None):
        response = requests.get(self._read_api.url(url), headers=headers)
        return HTTPTestResponse(response)

    def post(self, url, **message):
        return self.post_or_put('POST', url, **message)

    def put(self, url, **message):
        return self.post_or_put('PUT', url, **message)

    def post_or_put(self, method, url, **message):
        assert method in ('POST', 'PUT'), 'Only support POST, PUT'
        http_function = {
            'POST': requests.post,
            'PUT': requests.put
        }[method]

        headers = dict(message.get("headers", []))

        if "data" in message:
            headers.update({"Content-type": message['content_type']})
            response = http_function(
                self._write_api.url(url),
                data=message['data'],
                headers=headers,
                timeout=60,
            )
        elif "files" in message:
            response = http_function(
                self._write_api.url(url),
                files=message['files'],
                headers=headers,
                timeout=60,
            )
        else:
            raise Exception("Incorrect message")
        return HTTPTestResponse(response)

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

from features.support.support import BaseClient


class FlaskTestClient(BaseClient):
    def __init__(self, read_app, write_app):
        self._read_api = read_app.app.test_client()
        self._write_api = write_app.app.test_client()

        self._storage = read_app.db.mongo_database
        self._config = read_app.app.config

    def get(self, url, headers=None):
        return self._read_api.get(url, headers=headers)

    def post(self, url, **message):
        headers = dict(message.get("headers", []))
        if "data" in message:
            print("url: '{}', message: {}".format(url, message))
            response = self._write_api.post(
                url,
                data=message['data'],
                headers=headers,
                content_type=message['content_type'],
            )
        elif "files" in message:
            response = self._write_api.post(
                url,
                files=message['files'],
                headers=headers,
                content_type=message['content_type'],
            )
        else:
            raise Exception("Incorrect message")

        return response

    def storage(self):
        return self._storage

    def spin_down(self):
        self._config.from_object("backdrop.read.config.test")

    def set_config_parameter(self, name, value):
        self._config[name] = value

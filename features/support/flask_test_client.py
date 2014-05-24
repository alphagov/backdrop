from .support import BaseClient


class FlaskTestClient(BaseClient):
    def __init__(self, flask_app):
        self._client = flask_app.app.test_client()
        self._mongo_db = flask_app.storage._db
        self._config = flask_app.app.config

    def get(self, url, headers=None):
        return self._client.get(url, headers=headers)

    def post(self, url, **message):
        return self._client.post(url, **message)

    def put(self, url, **message):
        return self._client.put(url, **message)

    def delete(self, url, **message):
        return self._client.delete(url, **message)

    def spin_down(self):
        self._config.from_object("backdrop.read.config.test")

    def set_config_parameter(self, name, value):
        self._config[name] = value

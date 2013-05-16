class FlaskTestClient(object):
    def __init__(self, flask_app):
        self._client = flask_app.app.test_client()
        self._storage = flask_app.db.connection
        self._config = flask_app.app.config

    def get(self, url, headers=None):
        return self._client.get(url, headers=headers)

    def post(self, url, **message):
        return self._client.post(url, **message)

    def storage(self):
        return self._storage

    def before_scenario(self):
        pass

    def after_scenario(self):
        pass

    def spin_down(self):
        self._config.from_object(
            "backdrop.read.config.test"
        )
        pass

    def set_config_parameter(self, name, value):
        self._config[name] = value

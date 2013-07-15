import os
import subprocess
import time
import requests


def wait_until(condition, timeout=15, interval=0.1):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return
        time.sleep(interval)
    raise RuntimeError("timeout")


class BaseClient(object):
    def before_scenario(self):
        pass

    def after_scenario(self):
        pass

    def spin_down(self):
        pass


class Api(object):
    @classmethod
    def start_api(cls, app_name, port):
        _api = Api(app_name, port)
        _api.start()
        return _api

    def __init__(self, name, port):
        self._name = name
        self._port = port
        self._process = None

    def _run(self):
        return subprocess.Popen(
            ["python", "start.py", self._name, self._port],
            preexec_fn=os.setsid,
            stderr=subprocess.STDOUT, stdout=subprocess.PIPE
        )

    def start(self):
        if self._running():
            raise RuntimeError(
                "An api is already available on port %s "
                "BEFORE starting the process!" % self._port)

        self._process = self._run()
        wait_until(self._running)

    def _running(self):
        try:
            return requests.get(self.url('/_status')).status_code == 200
        except:
            return False

    def stop(self):
        if self._process:
            os.killpg(self._process.pid, 9)
            self._process.communicate()

    def url(self, path):
        return 'http://localhost:{0}{1}'.format(self._port, path)

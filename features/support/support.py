import os
import subprocess
import time
import requests


def wait_until(condition, timeout=3, interval=0.1):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return
        time.sleep(interval)
    raise RuntimeError("timeout")


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
        wait_until(self._started)

    def _started(self):
        try:
            return requests.get(self.url('/_status')).status_code == 200
        except:
            return False

    def stop(self):
        os.killpg(self._process.pid, 9)

    def url(self, path):
        return 'http://localhost:{0}{1}'.format(self._port, path)

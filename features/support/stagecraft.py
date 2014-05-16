from flask import Flask, Response, abort, json, request
from multiprocessing import Process
import requests

from features.support.support import wait_until


class StagecraftService(object):
    def __init__(self, port, routes):
        self.__port = port
        self.__routes = routes
        self.__app = Flask('fake_stagecraft')
        self.__proc = None

        @self.__app.route('/', defaults={'path': ''})
        @self.__app.route('/<path:path>')
        def catch_all(path):
            if path == "_is_fake_server_up":
                return Response('Yes', 200)

            path_and_query = path
            if len(request.query_string) > 0:
                path_and_query += '?{}'.format(request.query_string)

            key = (request.method, path_and_query)

            resp_item = self.__routes.get(key, None)
            if resp_item is None:
                abort(404)
            return Response(json.dumps(resp_item), mimetype='application/json')

    def add_routes(self, routes):
        self.__routes.update(routes)
        self.restart()

    def reset(self):
        self.__routes = dict()
        self.restart()

    def start(self):
        if self.stopped():
            self.__proc = Process(target=self._run)
            self.__proc.start()
            wait_until(self.running)

    def stop(self):
        if self.running():
            self.__proc.terminate()
            self.__proc.join()
            self.__proc = None
        wait_until(self.stopped)

    def restart(self):
        self.stop()
        self.start()

    def running(self):
        if self.__proc is None:
            return False
        try:
            url = 'http://127.0.0.1:{}/_is_fake_server_up'.format(self.__port)
            return requests.get(url).status_code == 200
        except:
            return False

    def stopped(self):
        return not self.running()

    def _run(self):
        # reloading is disabled to stop the Flask webserver starting up twice
        # when used in conjunction with multiprocessing
        self.__app.run(port=self.__port, use_reloader=False)

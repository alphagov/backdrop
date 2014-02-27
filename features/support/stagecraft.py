from flask import Flask, Response, json, request, jsonify
from multiprocessing import Process
import requests
from features.support.support import wait_until

class StagecraftService(object):
    def __init__(self, port, url_response_dict):
        self.__port = port
        self.__url = 'http://127.0.0.1:{0}'.format(self.__port)
        self.__url_response_dict = url_response_dict
        self.__app = Flask('fake_stagecraft')
        self.__app.debug = True

        @self.__app.route('/', defaults={'path': ''})
        @self.__app.route('/<path:path>')
        def catch_all(path):

            if path == "_status":
              return jsonify(status='ok', message='database seems fine')

            if len(request.query_string) == 0:
                key = (request.method, path)
            else:
                key = (request.method, path + '?' + request.query_string)

            resp_item = self.__url_response_dict[key]
            return Response(json.dumps(resp_item), mimetype='application/json')

    def start(self):
        self.__proc = Process(target=self._run)
        self.__proc.start()
        wait_until(self.__running)

    def __running(self):
        try:
            return requests.get('{0}{1}'.format(self.__url, '/_status')).status_code == 200
        except:
            return False

    def stop(self):
        if self.__running:
            self.__proc.terminate()
            self.__proc.join()

    def _run(self):
        self.__app.run(port=self.__port)


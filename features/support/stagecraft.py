from Queue import Empty
from multiprocessing import Process, Queue
import json
import time


import requests
from twisted.web import server, resource
from twisted.internet import reactor


class StagecraftService(object):
    def __init__(self, port):
        self.__port = port
        self.__queue = None

    def start(self):
        self.__queue = Queue()
        self.__proc = Process(target=self._run, args=(self.__queue,))
        self.__proc.start()

    def stop(self):
        self.__proc.terminate()
        self.__queue = None

    def _run(self, queue):
        site = server.Site(StagecraftResource(queue))

        reactor.listenTCP(self.__port, site)
        reactor.run()

    def create_bucket(self, bucket):
        if self.__queue is None:
            raise "server is not running"

        self.__queue.put(('bucket', bucket))

    def reset(self):
        if self.__queue is None:
            raise "server is not running"
        self.__queue.put(('reset', True))


class StagecraftResource(resource.Resource):
    isLeaf = True

    def __init__(self, queue):
        self.__queue = queue

    def _read_all_messages(self):
        while True:
            try:
                message, arg = self.__queue.get_nowait()
                if message == 'bucket':
                    self.set_bucket(arg)
                elif message == 'reset':
                    self.__bucket = None
            except Empty:
                return

    def set_bucket(self, bucket):
        self.__bucket = bucket

    def render_GET(self, request):
        self._read_all_messages()
        request.setHeader('Content-type', 'application/json')
        return json.dumps(self.__bucket)


if __name__ == '__main__':
    stagecraft = StagecraftService(8080)
    stagecraft.start()
    stagecraft.create_bucket({"foo":"bar"})
    
    time.sleep(0.5)

    result = requests.get('http://localhost:8080/data-sets/test-data-set')
    print(result)
    print(result.json())

    result = requests.get('http://localhost:8080/data-sets?data-group=test-data-group&data-set=test-data-set')
    print(result)
    print(result.json())

    stagecraft.stop()
    #result = requests.get('http://localhost:8080/foo/bar')
    #print(result)

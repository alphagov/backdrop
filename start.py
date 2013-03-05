from argh import arg
from argh.dispatching import dispatch_command

from performance_platform.write import api as write_api
from performance_platform.read import api as read_api


@arg('app', choices=['read', 'write'], help='The name of the app to start')
@arg('port', type=int, help='The port number to bind to')
def start_app(app, port):
    if app == 'read':
        read_api.start(port)
    else:
        write_api.start(port)

if __name__ == '__main__':
    dispatch_command(start_app)

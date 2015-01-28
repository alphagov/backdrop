from argh import arg
from argh.dispatching import dispatch_command


def load_app(name):
    if name == "read":
        from backdrop.read import api as app
    elif name == "write":
        from backdrop.write import api as app
    return app


APP_CHOICES = ['read', 'write']


@arg('name', choices=APP_CHOICES, help='The name of the app to start')
@arg('port', type=int, help='The port number to bind to')
def start_app(name, port):
    load_app(name).start(port)


if __name__ == '__main__':
    dispatch_command(start_app)

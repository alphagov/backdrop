import sys

from performance_platform.write import api as write_api
from performance_platform.read import api as read_api

def print_usage_and_exit():
    print('Usage: python {0} <read|write>')
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_usage_and_exit()

    if sys.argv[1] == 'read':
        read_api.start()
    elif sys.argv[1] == 'write':
        write_api.start()
    else:
        print_usage_and_exit()
from flask import Flask
import write.api
import read.api
import sys


def print_usage_and_exit():
    print "Usage: python %s <read|write>" % sys.argv[0]
    exit(-1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_usage_and_exit()

    if sys.argv[1] == 'read':
        read.api.start()
    elif sys.argv[1] == 'write':
        write.api.start()
    else:
        print_usage_and_exit()

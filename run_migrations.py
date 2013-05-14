"""
Run all migrations
"""
import imp
import os
import sys
import pymongo
from os.path import join
import logging

logging.basicConfig(level=logging.DEBUG)

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))


def load_config(env):
    config_path = os.path.join(ROOT_PATH, 'backdrop', 'write', 'config')
    fp = None
    try:
        sys.path.append(config_path)
        fp, pathname, description = imp.find_module(
            "backdrop/write/config/%s" % env)
        return imp.load_module(env, fp, pathname, description)
    finally:
        sys.path.pop()
        if fp:
            fp.close()


def get_database(config):
    client = pymongo.MongoClient(config.MONGO_HOST, config.MONGO_PORT)

    return client[config.DATABASE_NAME]


def get_migrations():
    migrations_path = join(ROOT_PATH, 'migrations')
    for migration_file in os.listdir(migrations_path):
        if migration_file.endswith('.py'):
            migration_path = join(migrations_path, migration_file)

            yield imp.load_source('migration', migration_path)


if __name__ == '__main__':

    config = load_config(os.getenv('GOVUK_ENV', 'development'))
    database = get_database(config)

    for migration in get_migrations():
        migration.up(database)

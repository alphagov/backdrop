"""
Run migrations

By default runs all migrations in order. If arguments are provided then
only migration files that match the arguments are run.

For example:

python run_migrations.py 001_add_week_start.py

Would only run the first migration.
"""
import imp
import os
import sys
from os.path import join
import logging
from backdrop.core.storage.mongo import MongoStorageEngine

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

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


def get_storage(config):
    return MongoStorageEngine(
        config.MONGO_HOSTS, config.MONGO_PORT, config.DATABASE_NAME)


def get_migrations(migration_files):
    migrations_path = join(ROOT_PATH, 'migrations')
    for migration_file in os.listdir(migrations_path):
        if not migration_file.endswith('.py'):
            continue
        if migration_files is None or migration_file in migration_files:
            migration_path = join(migrations_path, migration_file)

            yield imp.load_source('migration', migration_path)


if __name__ == '__main__':

    config = load_config(os.getenv('GOVUK_ENV', 'development'))
    storage = get_storage(config)

    migration_files = sys.argv[1:] or None

    for migration in get_migrations(migration_files):
        log.info("Running migration %s" % migration)
        migration.up(storage)

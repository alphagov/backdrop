#!/usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals

import json

import imp
import os
import sys
import logging

from backdrop.core.database import Database

log = logging.getLogger(__name__)

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))


def main():
    logging.basicConfig(level=logging.DEBUG)
    config = load_config(os.getenv('GOVUK_ENV', 'development'))
    database = get_database(config)

    records = []
    for data_set_metadata in get_all_metadata(database):
        records.append(data_set_metadata)
    print(json.dumps(records, indent=2))


def get_all_metadata(database):
    for metadata in database.get_collection('buckets').find():
        yield metadata


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
    return Database(
        config.MONGO_HOSTS, config.MONGO_PORT, config.DATABASE_NAME)


if __name__ == '__main__':
    main()

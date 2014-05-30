import os
import logging
import datetime
from itertools import imap

import pymongo
from pymongo.errors import AutoReconnect
from bson import Code

from .. import timeutils
from ... import statsd


logger = logging.getLogger(__name__)

__all__ = ['MongoStorageEngine']


def get_mongo_client(hosts, port):
    """Return an appropriate mongo client
    """
    client_list = ','.join(':'.join([host, str(port)]) for host in hosts)

    # We can't always guarantee we'll be on 'production'
    # so we allow jenkins to add the set as a variable
    # Some test environments / other envs have their own sets e.g. 'gds-ci'
    replica_set = os.getenv('MONGO_REPLICA_SET', 'production')

    if replica_set == '':
        return pymongo.MongoClient(client_list)
    else:
        return pymongo.MongoReplicaSetClient(
            client_list, replicaSet=replica_set)


class MongoStorageEngine(object):
    @classmethod
    def create(cls, hosts, port, database):
        return cls(get_mongo_client(hosts, port), database)

    def __init__(self, mongo, database):
        self._mongo = mongo
        self._db = mongo[database]

    def _coll(self, data_set_id):
        return self._db[data_set_id]

    def alive(self):
        return self._mongo.alive()

    def dataset_exists(self, dataset_id):
        return dataset_id in self._db.collection_names()

    def create_dataset(self, dataset_id, size):
        if size > 0:
            self._db.create_collection(dataset_id, capped=True, size=size)
        else:
            self._db.create_collection(dataset_id, capped=False)

    def get_last_updated(self, data_set_id):
        last_updated = self._coll(data_set_id).find_one(
            sort=[("_updated_at", pymongo.DESCENDING)])
        if last_updated and last_updated.get('_updated_at') is not None:
            return timeutils.utc(last_updated['_updated_at'])

    def empty(self, data_set_id):
        self._coll(data_set_id).remove({})

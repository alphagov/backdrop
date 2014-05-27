"""OK
Change user buckets in users collection to data_sets
We have this as separate module to the migration
due to problems with naming python modules starting with digits
"""
import logging


log = logging.getLogger(__name__)


def up(db):
    mongo_db = db._mongo['backdrop']
    users_collection = mongo_db['users']
    users = users_collection.find()
    for user in users:
        if 'buckets' in user:
            user['data_sets'] = user['buckets']
            del(user['buckets'])

            mongo_db['users'].remove(user['email'])
            mongo_db['users'].insert(user)

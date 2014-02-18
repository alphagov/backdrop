"""
Update realtime buckets to be capped at 4mb (4194304b), which gives us
about 2 weeks worth of query depth with a few days tolerance
"""
from backdrop.core import timeutils
import logging
log = logging.getLogger(__name__)

CAP_SIZE = 4194304


def get_realtime_collection_names(db):
    return [name for name in db.collection_names()
            if name.endswith("realtime")]


def remove_all_capped_references(db):
    mongo_db = db._mongo['backdrop']
    for record in mongo_db['buckets'].find():
        # log.info("item {0}".format(record))
        mongo_db['buckets'].update(
            {"name": record['name']},
            {"$set":
                {
                    "capped_size": None,
                }
             },
            upsert=False,
            multi=False)


def remove_old_versions(db, collection_name):
    mongo_db = db._mongo['backdrop']
    variants = get_temp_collection_names(collection_name)

    # import pdb;pdb.set_trace()

    for variant in variants.values():
        log.info("Dropping {0}".format(mongo_db[variant]))
        mongo_db[variant].drop()



def copy_down_collection(db, collection_name):
    mongo_db = db._mongo['backdrop']

    # Create new collection
    # import pdb;pdb.set_trace()
    new_collection_name = get_temp_collection_names(collection_name)["new"]

    # This collection should be temporary, clean up if we have a leftover
    mongo_db[new_collection_name].drop()

    # Now create it
    log.info("Creating new collection {0}".format(new_collection_name))
    mongo_db.create_collection(new_collection_name, capped=True, size=CAP_SIZE)

    # Order this by asc, so that when we copy in, oldest records are pushed
    # out first
    # import pdb;pdb.set_trace()
    log.info("Copying items from {0}...".format(collection_name))
    for item in mongo_db[collection_name].find():

        # Insert item into new bucket
        mongo_db[new_collection_name].insert(item)


# Update the reference to capped size in the buckets collection
def update_bucket_metadata(db, collection_name):
    mongo_db = db._mongo['backdrop']

    mongo_db['buckets'].update(
        {"name": collection_name},
        {"$set":
            {
                "capped_size": CAP_SIZE,
                "_updated_at":  timeutils.now()
            }
         },
        upsert=False,
        multi=False)


def rename_collection(db, original_collection_name):
    mongo_db = db._mongo['backdrop']
    old_collection_name = get_temp_collection_names(
        original_collection_name)['old']
    new_collection_name = get_temp_collection_names(
        original_collection_name)['new']

    # rename old collection
    log.info("Renaming collection from {0} to old name {1}".format(
        original_collection_name, old_collection_name))
    mongo_db[original_collection_name].rename(
        old_collection_name, dropTarget=True)

    # rename new collection
    log.info("Renaming bucket from {0} to new name {1}".format(
        new_collection_name, original_collection_name))
    mongo_db[new_collection_name].rename(
        original_collection_name, dropTarget=True)


def get_temp_collection_names(collection_name):
    return {
        "old": collection_name + "_009_migration_old",
        "new": collection_name + "_009_migration_new"
    }


def up(db):
    mongo_db = db._mongo['backdrop']

    # To start off, get rid of all references to caps in the metadata,
    # because they were all wrong
    remove_all_capped_references(db)

    realtime_collections_names = get_realtime_collection_names(db)

    for collection_name in realtime_collections_names:

        # Check if collection has already been capped
        # {u'capped': True, u'size': 4194304.0}
        stats = mongo_db[collection_name].options()
        if(stats.get('capped') is True and stats['size'] is 4194304.0):
            log.info("Skipping {0}, already capped at {1}".format(
                collection_name, stats['size']))
            continue

        log.info("Copying down items from {0}".format(collection_name))
        copy_down_collection(db, collection_name)

        # Rename collections
        rename_collection(db, collection_name)

        # Clean up by deleting 'old' collection
        mongo_db[get_temp_collection_names(collection_name)['old']].drop()

        # Change the cap_size reference in buckets collection
        update_bucket_metadata(db, collection_name)

        # Remove old/new versions
        remove_old_versions(db, collection_name)


        print("Finished copying {}".format(collection_name))
    print("All done <3")

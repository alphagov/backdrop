"""
Update realtime buckets to be capped at 4mb (4194304b), which gives us
about 2 weeks worth of query depth with a few days tolerance
"""
from backdrop.core import timeutils
import logging
log = logging.getLogger(__name__)

CAP_SIZE = 4194304


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


def remove_backup_versions(db, collection_name):
    mongo_db = db._mongo['backdrop']
    variants = get_temp_collection_names(collection_name)

    for variant in variants.values():
        mongo_db[variant].drop()


def get_realtime_collection_names(db):
    return [name for name in db.collection_names()
            if "realtime" in name]


def copy_down_collection(db, collection_name):
    mongo_db = db._mongo['backdrop']

    # Ensure backups and widows are removed
    remove_backup_versions(db, collection_name)

    # Create new collection
    new_collection_name = collection_name + "_new"

    # This collection should be temporary, clean up if we have a leftover
    mongo_db[new_collection_name].drop()
    mongo_db.create_collection(new_collection_name, capped=True, size=CAP_SIZE)

    # Order this by asc, so that when we copy in, oldest records are pushed
    # out first
    for item in db.get_collection(collection_name).find(
            sort=["_timestamp", "ascending"]):
        # log.info("Copying items in {0}".format(collection_name))

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
    backup_collection_name = get_temp_collection_names(
        original_collection_name)['backup']
    new_collection_name = get_temp_collection_names(
        original_collection_name)['new']

    # rename backup collection
    log.info("Renaming collection from {0} to backup name {1}".format(
        original_collection_name, backup_collection_name))
    mongo_db[original_collection_name].rename(
        backup_collection_name, dropTarget=True)

    # rename new collection
    log.info("Renaming bucket from {0} to new name {1}".format(
        new_collection_name, original_collection_name))
    mongo_db[new_collection_name].rename(
        original_collection_name, dropTarget=True)


def get_temp_collection_names(collection_name):
    return {
        "backup": collection_name + "_backup",
        "new": collection_name + "_new"
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
        if(stats['capped'] is True and stats['size'] is 4194304.0):
            log.info("Skipping {0}, already capped at {1}".format(
                collection_name, stats['size']))
            continue

        log.info("Copying down items from {0}".format(collection_name))
        copy_down_collection(db, collection_name)

        # Rename collections
        rename_collection(db, collection_name)

        # Clean up by deleting 'backup' collection
        mongo_db[get_temp_collection_names(collection_name)['backup']].drop()

        # Change the cap_size reference in buckets collection
        update_bucket_metadata(db, collection_name)

        print("Finished copying {}".format(collection_name))
    print("All done <3")

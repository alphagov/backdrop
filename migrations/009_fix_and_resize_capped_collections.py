"""
Clean up capped collections:

- Update realtime data-sets to be capped at 4mb (4194304b), which gives us
  about 2 weeks worth of query depth with a few days tolerance.
- Copy any non realtime collections that are capped into uncapped collections

"""
import logging
log = logging.getLogger(__name__)

CAP_SIZE = 4194304


def get_realtime_collection_names(mongo_db):
    return [name for name in mongo_db.collection_names()
            if name.endswith("realtime")]


def get_non_realtime_capped_collection_names(mongo_db):
    for name in mongo_db.collection_names():
        if not name.endswith("realtime"):
            stats = mongo_db[name].options()
            if stats.get('capped'):
                yield name


def get_temp_collection_names(mongo_db):
    return filter(is_temp_collection_name, mongo_db.collection_names())


def create_new_capped_collection(mongo_db, collection_name):
    log.info("Creating new capped collection {0}".format(collection_name))
    mongo_db.create_collection(collection_name, capped=True, size=CAP_SIZE)


def create_new_uncapped_collection(mongo_db, collection_name):
    log.info("Creating new uncapped collection {0}".format(collection_name))
    mongo_db.create_collection(collection_name, capped=False)


def copy_collection(mongo_db, collection_name_from, collection_name_to):
    """Copy all records from one mongodb collection to another"""
    log.info("Copying items from {0}...".format(collection_name_from))
    for item in mongo_db[collection_name_from].find():
        mongo_db[collection_name_to].insert(item)


def rename_collection(mongo_db, collection_name_from, collection_name_to):
    log.info("Renaming collection from {0} to old name {1}".format(
        collection_name_from, collection_name_to))
    mongo_db[collection_name_from].rename(
        collection_name_to, dropTarget=True)


def get_temp_names_for_collection(collection_name):
    """
    >>> get_temp_names_for_collection("foo")
    {'new': 'foo_009_migration_new', 'old': 'foo_009_migration_old'}
    """
    suffixes = get_temp_collection_suffixes()
    return {
        k: collection_name + v for k, v in suffixes.items()}


def get_temp_collection_suffixes():
    return {
        "old": "_009_migration_old",
        "new": "_009_migration_new"
    }


def is_temp_collection_name(collection_name):
    """
    >>> is_temp_collection_name("foo_009_migration_old")
    True
    >>> is_temp_collection_name("foo_009_migration_new")
    True
    >>> is_temp_collection_name("foo")
    False
    >>> # To get rid of some left over tables from an initial run
    >>> is_temp_collection_name("foo_backup")
    True
    """
    for suffix in get_temp_collection_suffixes().values():
        if collection_name.endswith(suffix):
            return True
    if collection_name.endswith("_backup"):
        return True
    return False


def remove_temporary_collections(mongo_db):
    """Remote any temporary collections that have been left hanging around"""
    log.info("Dropping temporary collections")
    for collection_name in get_temp_collection_names(mongo_db):
        log.info("Dropping temp collection {0}".format(collection_name))
        mongo_db[collection_name].drop()


def realtime_data_set_is_correctly_capped(mongo_db, collection_name):
    stats = mongo_db[collection_name].options()
    return stats.get('capped') is True and stats['size'] == CAP_SIZE


def up(db):
    # Depracated with the introducetion of MongoStorageEngine
    return None
    mongo_db = db._mongo['backdrop']

    remove_temporary_collections(mongo_db)

    # Correctly cap all realtime collections
    for collection_name in get_realtime_collection_names(mongo_db):
        if realtime_data_set_is_correctly_capped(mongo_db, collection_name):
            log.info("Skipping {0}, already correctly capped".format(
                collection_name))
            continue

        temp_names = get_temp_names_for_collection(collection_name)

        create_new_capped_collection(mongo_db, temp_names['new'])

        copy_collection(mongo_db, collection_name, temp_names['new'])

        rename_collection(mongo_db, collection_name, temp_names['old'])
        rename_collection(mongo_db, temp_names['new'], collection_name)

        mongo_db[temp_names['old']].drop()

        print("Finished capping {}".format(collection_name))

    # Uncap all capped non-realtime collections
    for collection_name in get_non_realtime_capped_collection_names(mongo_db):
        temp_names = get_temp_names_for_collection(collection_name)

        create_new_uncapped_collection(mongo_db, temp_names['new'])

        copy_collection(mongo_db, collection_name, temp_names['new'])

        rename_collection(mongo_db, collection_name, temp_names['old'])
        rename_collection(mongo_db, temp_names['new'], collection_name)

        mongo_db[temp_names['old']].drop()

        print("Finished uncapping {}".format(collection_name))

    print("All done <3")

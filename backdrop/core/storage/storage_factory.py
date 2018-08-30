from .mongo import MongoStorageEngine


def create_storage_engine(config):
    database_url = config['DATABASE_URL']
    storage = MongoStorageEngine.create(
        database_url,
        config.get('CA_CERTIFICATE')
    )

    return storage

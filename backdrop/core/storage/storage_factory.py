from .mongo import MongoStorageEngine
from .postgres import PostgresStorageEngine


def create_storage_engine(config):
    database_url = config['DATABASE_URL']
    database_engine = config['DATABASE_ENGINE']
    if database_engine == 'mongodb':
        storage = MongoStorageEngine.create(
            database_url,
            config.get('CA_CERTIFICATE')
        )
    elif database_engine == 'postgres':
        storage = PostgresStorageEngine(database_url)
    else:
        raise NotImplementedError(
            'Database engine not implemented "%s"' % database_engine)

    return storage

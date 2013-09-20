import json
import os
from invoke import task
from os import getenv
from backdrop.core import database
from backdrop.write.api import app
from backdrop.core.bucket import BucketConfig
from backdrop.core.repository import BucketConfigRepository


def environment():
    return getenv("GOVUK_ENV", "development")


def get_database(app):
    return database.Database(
        app.config['MONGO_HOST'],
        app.config['MONGO_PORT'],
        app.config['DATABASE_NAME']
    )


@task
def create_bucket(name, datagroup, datatype, rawqueries=False, token=None,
                  autoids=None, uploadformat=None, uploadfilters=None,
                  queryable=True, realtime=False):
    """Create a new bucket configuration in the database."""

    app.config.from_object(
        "backdrop.write.config.%s" % environment()
    )
    db = get_database(app)

    config = BucketConfig(name=name, data_group=datagroup, data_type=datatype,
                          raw_queries_allowed=rawqueries, bearer_token=token,
                          upload_format=uploadformat,
                          upload_filters=uploadfilters, auto_ids=autoids,
                          queryable=queryable, realtime=realtime)
    repository = BucketConfigRepository(db)

    repository.save(config)


@task
def load_seed():
    """One off task to generate seed data from current configuration"""

    seed_path = os.path.join(os.path.dirname(__file__), "config", "seed.json")
    with open(seed_path) as f:
        seed = json.load(f)

    app.config.from_object(
        "backdrop.write.config.%s" % environment()
    )
    db = get_database(app)

    repository = BucketConfigRepository(db)
    for bucket_json in seed:
        repository.save(BucketConfig(**bucket_json), create_bucket=False)

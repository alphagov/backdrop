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


def get_database():
    app.config.from_object(
        "backdrop.write.config.%s" % environment()
    )
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
    db = get_database()

    config = BucketConfig(name=name, data_group=datagroup, data_type=datatype,
                          raw_queries_allowed=rawqueries, bearer_token=token,
                          upload_format=uploadformat,
                          upload_filters=uploadfilters, auto_ids=autoids,
                          queryable=queryable, realtime=realtime)
    repository = BucketConfigRepository(db)

    repository.save(config)


@task
def load_seed():
    """One off task to load buckets and users from a seed file"""
    def load_seed_file(filename):
        seed_path = os.path.join(os.path.dirname(__file__), "config", filename)
        with open(seed_path) as f:
            return json.load(f)

    def save_all(filename, repo_cls, model_cls, **save_kwargs):
        repo = repo_cls(get_database())
        for item in load_seed_file(filename):
            repo.save(model_cls(**item), **save_kwargs)

    save_all("bucket-seed.json",
             BucketConfigRepository,
             BucketConfig, create_bucket=False)

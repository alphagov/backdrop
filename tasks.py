import json
import os
from invoke import task
from os import getenv
from backdrop.core import database
from backdrop.core.user import UserConfig
from backdrop.write.api import app
from backdrop.core.data_set import BucketConfig
from backdrop.core.repository import BucketConfigRepository,\
    UserConfigRepository


def environment():
    return getenv("GOVUK_ENV", "development")


def get_database():
    app.config.from_object(
        "backdrop.write.config.%s" % environment()
    )
    return database.Database(
        app.config['MONGO_HOSTS'],
        app.config['MONGO_PORT'],
        app.config['DATABASE_NAME']
    )


@task
def create_data_set(name, datagroup, datatype, rawqueries=False, token=None,
                  autoids=None, uploadformat=None, uploadfilters=None,
                  queryable=True, realtime=False):
    """Create a new data_set configuration in the database."""
    db = get_database()

    config = BucketConfig(name=name, data_group=datagroup, data_type=datatype,
                          raw_queries_allowed=rawqueries, bearer_token=token,
                          upload_format=uploadformat,
                          upload_filters=uploadfilters, auto_ids=autoids,
                          queryable=queryable, realtime=realtime)
    repository = BucketConfigRepository(db)

    repository.save(config)


@task
def allow_access(email, data_set):
    """Give a user access to a data_set."""
    db = get_database()

    repository = UserConfigRepository(db)

    config = repository.retrieve(email) or UserConfig(email)

    if data_set not in config.data_sets:
        config = UserConfig(email, config.data_sets + [data_set])
        repository.save(config)


@task
def load_seed():
    """One off task to load data_sets and users from seed files"""
    def load_seed_file(filename):
        seed_path = os.path.join(os.path.dirname(__file__), "config", filename)
        with open(seed_path) as f:
            return json.load(f)

    def save_all(filename, repo_cls, model_cls, **save_kwargs):
        repo = repo_cls(get_database())
        for item in load_seed_file(filename):
            repo.save(model_cls(**item), **save_kwargs)

    save_all("data_set-seed.json",
             BucketConfigRepository,
             BucketConfig, create_data_set=False)
    save_all("user-seed.json",
             UserConfigRepository,
             UserConfig)

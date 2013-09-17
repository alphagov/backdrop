import json
from invoke import task
from os import getenv
from backdrop.core import database
from backdrop.write.api import app
from backdrop.core.bucket import BucketConfig
from backdrop.core.repository import BucketRepository


def environment():
    return getenv("GOVUK_ENV", "development")


@task
def create_bucket(name, datagroup, datatype, rawqueries=False, token=None,
                  autoids=None, uploadformat=None, uploadfilters=None,
                  queryable=True, realtime=False):

    app.config.from_object(
        "backdrop.write.config.%s" % environment()
    )
    db = database.Database(
        app.config['MONGO_HOST'],
        app.config['MONGO_PORT'],
        app.config['DATABASE_NAME']
    )

    config = BucketConfig(name=name, data_group=datagroup, data_type=datatype,
                          raw_queries_allowed=rawqueries, bearer_token=token,
                          upload_format=uploadformat,
                          upload_filters=uploadfilters, auto_ids=autoids,
                          queryable=queryable, realtime=realtime)
    repository = BucketRepository(db.get_collection("buckets"))

    repository.save(config)


@task
def generate_seed():
    """One off task to generate seed data from current configuration"""
    seed = []
    env = environment()
    app.config.from_object("backdrop.write.config.%s" % env)
    app.config.from_object("backdrop.read.config.%s" % env)

    def config_for(name):
        return {
            "name": name,
            "data_group": "group_%s" % name,
            "data_type": "type_%s" % name,
            "raw_queries_allowed": app.config["RAW_QUERIES_ALLOWED"]
            .get(name, False),
            "bearer_token": app.config["TOKENS"].get(name),
            "upload_format": app.config["BUCKET_UPLOAD_FORMAT"].get(name),
            "upload_filters": app.config["BUCKET_UPLOAD_FILTERS"].get(name),
            "auto_ids": app.config["BUCKET_AUTO_ID_KEYS"].get(name),
            "queryable": True,
            "realtime": False
        }

    for name in app.config["TOKENS"]:
        seed.append(config_for(name))

    for name in app.config["BUCKET_UPLOAD_FORMAT"]:
        seed.append(config_for(name))

    with open('seed.json', 'w') as outfile:
        json.dump(seed, outfile)

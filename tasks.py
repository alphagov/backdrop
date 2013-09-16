from invoke import task
from os import getenv
from backdrop.core import database
from backdrop.write.api import app
from backdrop.core.bucket import BucketConfig
from backdrop.core.repository import BucketRepository

def environment():
    return getenv("GOVUK_ENV", "development")

@task
def create_bucket(name, service, datatype, rawqueries=False, token=None,
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

    config = BucketConfig(name=name, service=service, data_type=datatype,
                          raw_queries_allowed=rawqueries, bearer_token=token,
                          upload_format=uploadformat, upload_filters=uploadfilters,
                          auto_ids=autoids, queryable=queryable, realtime=realtime)
    repository = BucketRepository(db.get_collection("buckets"))

    repository.save(config)

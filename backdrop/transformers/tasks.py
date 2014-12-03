from celery import Celery

# Load the appropriate config from backdrop.write
import importlib
from os import getenv

GOVUK_ENV = getenv("GOVUK_ENV", "development")
config = importlib.import_module(
    "backdrop.write.config.{}".format(GOVUK_ENV))

app = Celery(
    'transformations',
    broker=config.TRANSFORMER_AMQP_URL,
    include=['backdrop.transformers.tasks'])


@app.task(ignore_result=True)
def dispatch(dataset_id):
    """
    For the given parameters, query stagecraft for transformations
    to run, and dispatch tasks to the appropriate workers.
    """

    # TODO: query stagecraft with dataset_id and run transforms
    pass

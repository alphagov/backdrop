from celery import Celery

# Load the appropriate config file as a python module
import importlib
from os import getenv

ENVIRONMENT = getenv("ENVIRONMENT", "development")
config = importlib.import_module(
    "backdrop.transformers.config.{}".format(ENVIRONMENT))

app = Celery(
    'transformations',
    broker=config.TRANSFORMER_AMQP_URL,
    include=['backdrop.transformers.dispatch'])


if __name__ == '__main__':
    app.start()

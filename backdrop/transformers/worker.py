from celery import Celery

# Load the appropriate config file as a python module
import importlib
from os import getenv
GOVUK_ENV = getenv("GOVUK_ENV", "development")
config = importlib.import_module("backdrop.write.config.{}".format(GOVUK_ENV))

app = Celery(
    'transformations',
    broker=config.TRANSFORMER_AMQP_URL,
    include=['backdrop.transformers.tasks'])

if __name__ == '__main__':
    app.start()

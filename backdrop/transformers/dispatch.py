import logging

from worker import app, config

from performanceplatform.client import AdminAPI


logger = logging.getLogger(__name__)


@app.task(ignore_result=True)
def entrypoint(dataset_id, earliest, latest):
    """
    For the given parameters, query stagecraft for transformations
    to run, and dispatch tasks to the appropriate workers.
    """

    admin_api = AdminAPI(
        config.STAGECRAFT_URL,
        config.STAGECRAFT_OAUTH_TOKEN,
    )

    transforms = admin_api.get_data_set_transforms(dataset_id)

    for transform in transforms:
        app.send_task(
            'backdrop.transformers.dispatch.run_transform',
            args=(dataset_id, transform, earliest, latest)
        )


@app.task(ignore_result=True)
def run_transform(dataset_id, transform, earliest, latest):
    logger.info(dataset_id, transform, earliest, latest)
    pass

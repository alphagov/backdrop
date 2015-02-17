import importlib
import logging
import pytz

from datetime import datetime
from os import getenv

from statsd import StatsClient

from backdrop.core.timeseries import parse_period
from backdrop.core.log_handler import get_log_file_handler
from backdrop.core.errors import incr_on_error

from worker import app, config

from performanceplatform.client import AdminAPI, DataSet

GOVUK_ENV = getenv("GOVUK_ENV", "development")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(
    get_log_file_handler("log/{}.log".format(GOVUK_ENV), logging.DEBUG))

stats_client = StatsClient(prefix=getenv("GOVUK_STATSD_PREFIX",
                                         "pp.apps.backdrop.transformers.worker"))


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
    data_set_config = admin_api.get_data_set_by_name(dataset_id)

    for transform in transforms:
        app.send_task(
            'backdrop.transformers.dispatch.run_transform',
            args=(data_set_config, transform, earliest, latest)
        )
        stats_client.incr('dispatch')


def _now():
    now = datetime.utcnow()
    now = now.replace(tzinfo=pytz.utc)
    return now


def get_query_parameters(transform, earliest, latest):
    query_parameters = transform.get('query-parameters', {})
    query_parameters['flatten'] = 'true'

    if earliest == latest:
        if 'period' in query_parameters:
            query_parameters['duration'] = 1
            query_parameters['start_at'] = latest.isoformat()
        else:
            query_parameters['inclusive'] = 'true'
            query_parameters['start_at'] = earliest.isoformat()
            query_parameters['end_at'] = latest.isoformat()
    else:
        if 'period' in query_parameters:
            period = parse_period(query_parameters['period'])
            start_at = period.start(earliest).isoformat()
            end_datetime = period.end(latest)

            if end_datetime > _now():
                end_datetime = period.start(latest)

            end_at = end_datetime.isoformat()
        else:
            start_at = earliest.isoformat()
            end_at = latest.isoformat()

        query_parameters['inclusive'] = 'true'
        query_parameters['start_at'] = start_at
        query_parameters['end_at'] = end_at

    return query_parameters


def get_transform_function(transform):
    function_namespace = transform['type']['function']
    function_name = function_namespace.split('.')[-1]
    module_namespace = '.'.join(function_namespace.split('.')[:-1])

    transform_module = importlib.import_module(module_namespace)
    return getattr(transform_module, function_name)


def get_or_get_and_create_output_dataset(transform, input_dataset):
    output_group = transform['output'].get(
        'data-group', input_dataset['data_group'])
    output_type = transform['output']['data-type']

    admin_api = AdminAPI(
        config.STAGECRAFT_URL,
        config.STAGECRAFT_OAUTH_TOKEN,
    )
    output_data_set_config = admin_api.get_data_set(output_group, output_type)
    if not output_data_set_config:
        data_set_config = dict(input_dataset.items() + {
            'data_type': output_type,
            'data_group': output_group,
        }.items())
        del(data_set_config['name'])
        output_data_set_config = admin_api.create_data_set(data_set_config)

    return DataSet.from_group_and_type(
        config.BACKDROP_WRITE_URL,
        output_group,
        output_type,
        token=output_data_set_config['bearer_token'],
    )


@app.task(ignore_result=True)
@stats_client.timer('run_transform')
@incr_on_error(stats_client, 'run_transform.error')
def run_transform(data_set_config, transform, earliest, latest):
    data_set = DataSet.from_group_and_type(
        config.BACKDROP_READ_URL,
        data_set_config['data_group'],
        data_set_config['data_type'],
    )

    data = data_set.get(
        query_parameters=get_query_parameters(transform, earliest, latest)
    )

    transform_function = get_transform_function(transform)
    transformed_data = transform_function(data['data'],
                                          transform,
                                          data_set_config)

    output_data_set = get_or_get_and_create_output_dataset(
        transform,
        data_set_config)
    output_data_set.post(transformed_data)

    stats_client.incr('run_transform.success')

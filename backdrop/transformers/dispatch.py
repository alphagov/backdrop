import importlib
import logging

from worker import app, config

from performanceplatform.client import AdminAPI, DataSet


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
    data_set_config = admin_api.get_data_set_by_name(dataset_id)

    for transform in transforms:
        app.send_task(
            'backdrop.transformers.dispatch.run_transform',
            args=(data_set_config, transform, earliest, latest)
        )


@app.task(ignore_result=True)
def run_transform(data_set_config, transform, earliest, latest):
    data_set = DataSet.from_group_and_type(
        config.BACKDROP_READ_URL,
        data_set_config['data_group'],
        data_set_config['data_type'],
    )

    query_parameters = transform.get('query-parameters', {})
    query_parameters['flatten'] = 'true'
    query_parameters['start_at'] = earliest
    query_parameters['end_at'] = latest

    data = data_set.get(query_parameters=query_parameters)

    function_namespace = transform['type']['function']
    function_name = function_namespace.split('.')[-1]
    module_namespace = '.'.join(function_namespace.split('.')[:-1])

    transform_module = importlib.import_module(module_namespace)
    transform_function = getattr(transform_module, function_name)

    transformed_data = transform_function(data['data'], transform['options'])

    output_group = transform['output'].get(
        'data-group', data_set_config['data_group'])
    output_type = transform['output']['data-type']

    admin_api = AdminAPI(
        config.STAGECRAFT_URL,
        config.STAGECRAFT_OAUTH_TOKEN,
    )
    output_data_set_config = admin_api.get_data_set(output_group, output_type)

    output_data_set = DataSet.from_group_and_type(
        config.BACKDROP_WRITE_URL,
        output_group,
        output_type,
        token=output_data_set_config['bearer_token'],
    )
    output_data_set.post(transformed_data)

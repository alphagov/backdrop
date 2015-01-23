import string

from .util import encode_id
from ..worker import config

from performanceplatform.client import AdminAPI, DataSet

data_type_to_value_mappings = {
    'completion-rate': 'rate',
    'digital-takeup': 'rate',
    'user-satisfaction-score': 'score',
}


def get_read_params(transform_params, latest_timestamp):
    read_params = {}
    if 'period' in transform_params:
        read_params['duration'] = 1
        read_params['period'] = transform_params['period']
    else:
        read_params['start_at'] = latest_timestamp
    read_params['sort_by'] = '_timestamp:descending'
    return read_params


def is_latest_data(data_set_config, transform, latest_datum):
    """
    Read from backdrop to determine if new data is the latest.
    """

    data_set = DataSet.from_group_and_type(
        config.BACKDROP_READ_URL,
        data_set_config['data_group'],
        data_set_config['data_type']
    )

    transform_params = transform.get('query_parameters', {})
    read_params = get_read_params(transform_params, latest_datum['_timestamp'])
    existing_data = data_set.get(query_parameters=read_params)

    if existing_data['data']:
        if existing_data['data'][0]['_timestamp'] > latest_datum['_timestamp']:
            return False

    return True


def compute(new_data, transform, data_set_config):

    # Sort the new data by timestamp and use the latest data point.
    new_data.sort(key=lambda item: item['_timestamp'], reverse=True)
    latest_datum = new_data[0]

    # Only continue if we are not back filling data.
    if not is_latest_data(data_set_config, transform, latest_datum):
        return []

    # Input data won't have a unique key for each type of value.
    # E.g. completion rate and digital takeup are both "rate".
    # Use the data_type as the value key in the output, and map
    # the data_type to the expected key to get the value.
    value_key = data_type_to_value_mappings[data_set_config['data_type']]

    # A dataset may be present on multiple dashboards. Produce a
    # latest value for each published dashboard, keyed by slug.
    admin_api = AdminAPI(config.STAGECRAFT_URL, config.STAGECRAFT_OAUTH_TOKEN)
    latest_values = []
    configs = admin_api.get_data_set_dashboard(data_set_config['name'])

    # New dataset name convention uses underscores.
    data_type = string.replace(data_set_config['data_type'], '-', '_')

    for dashboard_config in configs:
        if dashboard_config['published'] and latest_datum[value_key] is not None:
            slug = dashboard_config['slug']
            id = encode_id(slug, data_type)
            latest_values.append({
                '_id': id,
                'dashboard_slug': slug,
                data_type: latest_datum[value_key],
                '_timestamp': latest_datum['_timestamp'],
            })

    return latest_values

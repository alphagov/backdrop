import base64
import string

from ..worker import config

from performanceplatform.client import AdminAPI, DataSet

data_type_to_value_mappings = {
    'completion-rate': 'rate',
    'digital-takeup': 'rate',
    'user-satisfaction-score': 'score',
}


def compute(new_data, transform, data_set_config):

    # Sort the new data by timestamp and use the latest data point.
    new_data.sort(key=lambda item: item['_timestamp'], reverse=True)
    latest_datum = new_data[0]

    # Read from the backdrop API to determine if new data is the latest.
    data_set = DataSet.from_group_and_type(
        config.BACKDROP_READ_URL,
        data_set_config['data_group'],
        data_set_config['data_type']
    )

    transform_params = transform.get('query_parameters', {})
    read_params = {}
    if 'period' in transform_params:
        read_params['duration'] = 1
        read_params['period'] = transform_params['period']
    else:
        read_params['_start_at'] = latest_datum['_timestamp']

    existing_data = data_set.get(query_parameters=read_params)

    # Fall-through case is that there is no existing data in the data set -
    # so the data just written must be the latest.
    if existing_data['data']:
        if 'period' in transform_params:
            if existing_data['data'][0]['_start_at'] > latest_datum['_timestamp']:
                return []
        else:
            # If we got more than one data point back, assume latest_data
            # isn't the newest in the dataset.
            if len(existing_data['data']) > 1:
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
            id = base64.b64encode(slug + data_type)
            latest_values.append({
                '_id': id,
                'dashboard_slug': slug,
                data_type: latest_datum[value_key],
                '_timestamp': latest_datum['_timestamp'],
            })

    return latest_values

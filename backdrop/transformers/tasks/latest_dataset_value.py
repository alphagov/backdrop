import base64
import string

from ..worker import config

from performanceplatform.client import AdminAPI

data_type_to_value_mappings = {
    'completion-rate': 'rate',
    'digital-takeup': 'rate',
    'user-satisfaction-score': 'score',
}


def compute(data, options, data_set_config):

    admin_api = AdminAPI(
        config.STAGECRAFT_URL,
        config.STAGECRAFT_OAUTH_TOKEN)

    data_type = string.replace(data_set_config['data_type'], '-', '_')

    # Sort the incoming data by timestamp and use the latest
    data.sort(key=lambda item: item['_timestamp'], reverse=True)
    latest_datum = data[0]

    # Input data won't have a unique key for each type of value.
    # E.g. completion rate and digital takeup are both "rate".
    # Use the data_type as the value key in the output, and map
    # the data_type to the expected key to get the value.
    value_key = data_type_to_value_mappings[data_set_config['data_type']]

    # A dataset may be present on multiple dashboards. Produce a
    # latest value for each published dashboard, keyed by slug.
    # TODO: ensure the latest data point is used.
    latest_values = []
    configs = admin_api.get_data_set_dashboard(data_set_config['name'])

    for dashboard_config in configs:
        if dashboard_config['published']:
            slug = dashboard_config['slug']
            id = base64.b64encode(slug + data_type)
            latest_values.append({
                '_id': id,
                'dashboard_slug': slug,
                data_type: latest_datum[value_key],
                '_timestamp': latest_datum['_timestamp'],
            })

    return latest_values

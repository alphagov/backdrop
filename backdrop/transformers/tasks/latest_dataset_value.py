import base64

from ..worker import config

from performanceplatform.client import AdminAPI

data_type_to_value_mappings = {
    'completion_rate': 'rate',
    'digital_takeup': 'rate',
    'user_satisfaction_score': 'score',
}


def compute(data, options, data_set_config):

    admin_api = AdminAPI(
        config.STAGECRAFT_URL,
        config.STAGECRAFT_OAUTH_TOKEN)
    dashboard_config = admin_api.get_data_set_dashboard(
        data_set_config['name'])
    data_type = data_set_config['data_type']
    id = base64.b64encode(dashboard_config['slug'] + data_type)

    # Sort the incoming data by timestamp and use the latest
    data.sort(key=lambda item: item['_timestamp'], reverse=True)
    latest_datum = data[0]

    # Input data won't have a unique key for each type of value.
    # E.g. completion rate and digital takeup are both "rate".
    # Use the data_type as the value key in the output, and map
    # the data_type to the expected key to get the value.
    value_key = data_type_to_value_mappings[data_type]

    latest_value = {
        '_id': id,
        'dashboard-slug': dashboard_config['slug'],
        data_type: latest_datum[value_key],
        '_timestamp': latest_datum['_timestamp'],
    }

    # Query mongo by that ID and parse the timestamp
    # Determine if we have any new dat
    # Update the data set if we do

    # Return a datapoint for the aggregated dataset
    return latest_value

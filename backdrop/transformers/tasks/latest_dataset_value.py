import base64

from ..worker import config

from performanceplatform.client import AdminAPI


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

    latest_value = {
        '_id': id,
        'dashboard-slug': dashboard_config['slug'],
        data_type: latest_datum[data_type],
        '_timestamp': latest_datum['_timestamp'],
    }

    # Query mongo by that ID and parse the timestamp
    # Determine if we have any new dat
    # Update the data set if we do

    # Return a datapoint for the aggregated dataset
    return latest_value

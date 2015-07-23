import string

from .util import encode_id, is_latest_data, _get_read_params
from ..worker import config

from performanceplatform.client import AdminAPI
from performanceplatform.client import DataSet

data_type_to_value_mappings = {
    'completion-rate': 'rate',
    'digital-takeup': 'rate',
    'user-satisfaction-score': 'score',
}

# because collected data does not have a type
# user sat, completiton rate - collected. digital takeup both collected and tx ex
# start ignore digital_takeup is the change?
metric_to_period_mappings = {
    'digital_cost_per_transaction': 'quarterly',
    'digital_takeup': 'quarterly'
    #everything else : seasonally-adjusted
}


def data_is_released(data_set_config,
                     transform,
                     latest_datum):
    latest_aggregate_data = \
        (transform['output']['data-group'] == 'service-aggregates' and
         transform['output']['data-type'] == 'latest-dataset-value')
    if latest_aggregate_data:

        data_set = DataSet.from_group_and_type(
            config.BACKDROP_READ_URL,
            data_set_config['data_group'],
            data_set_config['data_type']
        )
        generated_read_params = _get_read_params(
            {}, latest_datum['_timestamp'])

        # Checks against all of type that this is not newer than the type.
        # If there is already data for this service id we will never get here.
        additional_read_params = {'filter_by': 'type:{}'.format(
            latest_datum['type'])}
        read_params = dict(
            generated_read_params.items() + additional_read_params.items())
        existing_data = data_set.get(query_parameters=read_params)
        if existing_data['data']:
            if(existing_data['data'][0]['_timestamp'] <
               latest_datum['_timestamp']):
                return False
    return True


def compute(new_data, transform, data_set_config):

    # Sort the new data by timestamp and use the latest data point.
    new_data.sort(key=lambda item: item['_timestamp'], reverse=True)
    latest_datum = new_data[0]

    # Only continue if we are not back filling data.
    is_latest = is_latest_data(
        data_set_config, transform, latest_datum)
    if not is_latest:
        pass

    # This check ensures that we do not post data newer than the newest
    # transactions explorer spreadsheet data for the type to
    # service-aggregates/latest-dataset-values
    if not data_is_released(data_set_config, transform, latest_datum):
        pass

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
        if(dashboard_config['published']
           and latest_datum[value_key] is not None):
            slug = dashboard_config['slug']
            id = encode_id(slug, data_type)
            latest_values.append({
                '_id': id,
                'dashboard_slug': slug,
                data_type: latest_datum[value_key],
                '_timestamp': latest_datum['_timestamp'],
            })

    return latest_values

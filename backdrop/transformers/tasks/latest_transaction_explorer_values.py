from ..worker import config

from performanceplatform.client import AdminAPI

from .util import encode_id, group_by, is_latest_data

REQUIRED_DATA_POINTS = [
    {'name': "cost_per_transaction", 'ignore': 'quarterly'},
    {'name': "digital_cost_per_transaction", 'ignore': None},
    {'name': "digital_takeup", 'ignore': None},
    {'name': "number_of_digital_transactions", 'ignore': 'quarterly'},
    {'name': "number_of_transactions", 'ignore': 'quarterly'},
    {'name': "total_cost", 'ignore': 'quarterly'},
]

ADDITIONAL_FIELDS = [
    "end_at",
    "period",
    "service_id",
    "type"
]

admin_api = AdminAPI(
    config.STAGECRAFT_URL,
    config.STAGECRAFT_OAUTH_TOKEN)


# sorting should now be maintained from the initial sort
# we still run this function so that we can set an empty dict
# when a service doesn't have the latest data - without preserving as
# many service ids as possible we would have lots of things without
# data points. Now we will have lots with data points but the data
# will be none.
def _get_latest_data_point(sorted_data, data_point_name):
    def _use_data_point(data_point, name, ignore):
        should_not_be_ignored = (ignore != data_point['type'])
        return should_not_be_ignored

    name = data_point_name['name']
    ignore = data_point_name['ignore']

    for data_point in sorted_data:
        if _use_data_point(data_point, name, ignore):
            return data_point
    return None


def _up_to_date(latest_data_points,
                latest_quarter,
                latest_seasonally_adjusted):
    if latest_data_points['type'] == 'seasonally-adjusted':
        return latest_data_points['_timestamp'] == latest_seasonally_adjusted
    else:
        return latest_data_points['_timestamp'] == latest_quarter


def _get_stripped_down_data_for_data_point_name_only(
        dashboard_config,
        latest_data_points,
        data_point_name,
        latest_quarter,
        latest_seasonally_adjusted):
    """
    Builds up backdrop ready datum for a single transaction explorer metric.

    It does this by iterating through the passed in data_point_name
    and building up a new dict based on
    these key: value pairings. We then loop through additional fields and add
    those if present. If a required_field is not found we return
    a dict with a value of None for this data_point.
    """
    required_fields = [data_point_name['name']]
    new_data = {}
    for field in required_fields:
        if field in latest_data_points and _up_to_date(
                latest_data_points,
                latest_quarter,
                latest_seasonally_adjusted):
            new_data[field] = latest_data_points[field]
        else:
            new_data[field] = None
    for field in ADDITIONAL_FIELDS:
        if field in latest_data_points:
            new_data[field] = latest_data_points[field]
    new_data['dashboard_slug'] = dashboard_config['slug']

    if latest_data_points['type'] == 'seasonally-adjusted':
        new_data['_timestamp'] = latest_seasonally_adjusted
    else:
        new_data['_timestamp'] = latest_quarter

    new_data['_id'] = encode_id(
        new_data['dashboard_slug'],
        data_point_name['name'])
    return new_data


def _service_ids_with_data(data):
    return group_by('service_id', data).items()


def _get_dashboard_config(service_id):
    return admin_api.get_dashboard_by_tx_id(service_id)


def _get_dashboard_configs_with_data(ids_with_data):
    dashboard_configs_with_data = []
    for service_id, data in ids_with_data:
        dashboard_configs = _get_dashboard_config(service_id)
        for dashboard_config in dashboard_configs:
            dashboard_configs_with_data.append((dashboard_config, data))
    return dashboard_configs_with_data


def _get_data_points_for_each_tx_metric(data, transform, data_set_config):
    data_ordered_by_timestamp = sorted(
        data, key=lambda k: k['_timestamp'], reverse=True)
    quarterly_data_ordered_by_timestamp = \
        [datum for datum in data_ordered_by_timestamp
         if datum['type'] == 'quarterly']
    seasonally_adjusted_data_ordered_by_timestamp = \
        [datum for datum in data_ordered_by_timestamp
         if datum['type'] == 'seasonally-adjusted']
    latest_quarter = quarterly_data_ordered_by_timestamp[0]['_timestamp']
    latest_seasonally_adjusted = \
        seasonally_adjusted_data_ordered_by_timestamp[0]['_timestamp']

    ids_with_data = _service_ids_with_data(data_ordered_by_timestamp)
    dashboard_configs_with_data = _get_dashboard_configs_with_data(
        ids_with_data)

    for data_point_name in REQUIRED_DATA_POINTS:
        for dashboard_config, dashboard_data in dashboard_configs_with_data:
            latest_data = _get_latest_data_point(
                dashboard_data,
                data_point_name)
            if not latest_data:
                continue
            datum = _get_stripped_down_data_for_data_point_name_only(
                dashboard_config, latest_data, data_point_name,
                latest_quarter,
                latest_seasonally_adjusted)
            # we need to look at whether this is later than the latest
            # data currently present on the output data set as
            # for things like digital-takeup the  transactions explorer
            # dataset is not the only source.
            if datum and is_latest_data(
                    {'data_group': transform['output']['data-group'],
                     'data_type': transform['output']['data-type']},
                    transform,
                    datum,
                    # filter by record id as this is a hash of dashboard_slug
                    # and data_point_name and is therefore the important
                    # identifier of newer data
                    additional_read_params={
                        'filter_by': '_id:{}'.format(
                            datum['_id'])}):
                yield datum


def compute(data, transform, data_set_config=None):
    return [datum for datum
            in _get_data_points_for_each_tx_metric(
                data,
                transform,
                data_set_config)]

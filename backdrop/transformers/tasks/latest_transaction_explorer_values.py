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

REQUIRED_FIELDS = [
    "_timestamp",
]

admin_api = AdminAPI(
    config.STAGECRAFT_URL,
    config.STAGECRAFT_OAUTH_TOKEN)


def _get_latest_data_point(data, data_point_name):
    def _use_data_point(data_point, name, ignore):
        has_data = (name in data_point and data_point[name])
        should_not_be_ignored = (ignore != data_point['type'])
        return has_data and should_not_be_ignored

    name = data_point_name['name']
    ignore = data_point_name['ignore']

    data.sort(key=lambda item: item['_timestamp'], reverse=True)
    for data_point in data:
        if _use_data_point(data_point, name, ignore):
            return data_point
    return None


def _get_stripped_down_data_for_data_point_name_only(
        dashboard_config,
        latest_data_points,
        data_point_name):
    """
    Builds up backdrop ready datum for a single transaction explorer metric.

    It does this by iterating through the passed in data_point_name
    and all the REQUIRED_FIELDS and building up a new dict based on
    these key: value pairings. We then loop through additional fields and add
    those if present. If a REQUIRED_FIELD is not found we return None for
    this data_point.
    """
    required_fields = REQUIRED_FIELDS + [data_point_name['name']]
    new_data = {}
    for field in required_fields:
        if field in latest_data_points:
            new_data[field] = latest_data_points[field]
        else:
            return None
    for field in ADDITIONAL_FIELDS:
        if field in latest_data_points:
            new_data[field] = latest_data_points[field]
    import pdb; pdb.set_trace()
    new_data['dashboard_slug'] = dashboard_config['slug']
    new_data['_id'] = encode_id(
        new_data['dashboard_slug'],
        data_point_name['name'])
    return new_data


def _service_ids_with_data(data):
    return group_by('service_id', data).items()


def _get_dashboard_config(service_id):
    dashboard_configs = admin_api.get_dashboard_by_tx_id(service_id)
    if dashboard_configs:
        return dashboard_configs[0]
    else:
        return None


def _get_dashboard_configs_with_data(ids_with_data):
    dashboard_configs_with_data = []
    for service_id, data in ids_with_data:
        dashboard_config = _get_dashboard_config(service_id)
        if dashboard_config:
            dashboard_configs_with_data.append((dashboard_config, data))
    return dashboard_configs_with_data


def _get_data_points_for_each_tx_metric(data, transform, data_set_config,
                                        dashboard_config):
    ids_with_data = _service_ids_with_data(
        data)
    dashboard_data = ids_with_data[0][1]
    for data_point_name in REQUIRED_DATA_POINTS:
        latest_data = _get_latest_data_point(
            dashboard_data,
            data_point_name)
        if not latest_data:
            continue
        datum = _get_stripped_down_data_for_data_point_name_only(
            dashboard_config, latest_data, data_point_name)
        # we need to look at whether this is later than the latest
        # data currently present on the output data set as
        # for things like digital-takeup the  transactions explorer
        # dataset is not the only source.
        if datum and is_latest_data(
                {'data_group': transform['output']['data-group'],
                 'data_type': transform['output']['data-type']},
                transform,
                datum,
                additional_read_params={
                    'filter_by': 'dashboard_slug:{}'.format(
                        datum['dashboard_slug'])}):
            yield datum


def compute(data, transform, dashboard_config, data_set_config=None):
    return [datum for datum
            in _get_data_points_for_each_tx_metric(
                data,
                transform,
                data_set_config,
                dashboard_config)]

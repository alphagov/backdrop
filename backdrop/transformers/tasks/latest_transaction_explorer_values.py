from ..worker import config

from performanceplatform.client import AdminAPI

from .util import encode_id, group_by

required_data_points = [
    "cost_per_transaction",
    "digital_cost_per_transaction",
    "digital_takeup",
    "number_of_digital_transactions",
    "number_of_transactions",
    "total_cost",
]

required_fields = [
    "_timestamp",
    "end_at",
    "period",
    "service_id",
    "type"
]


def compute(data, options, data_set_config=None):

    admin_api = AdminAPI(
        config.STAGECRAFT_URL,
        config.STAGECRAFT_OAUTH_TOKEN)

    def get_latest_data_points(data):
        data.sort(key=lambda item: item['_timestamp'])
        return data

    def get_stripped_down_data_for_data_point_name_only(
            dashboard_config,
            latest_data_points,
            data_point_name):
        most_recent_data = latest_data_points[0]
        all_fields = required_fields + [data_point_name]
        new_data = {}
        for field in all_fields:
            new_data[field] = most_recent_data[field]
        new_data['dashboard_slug'] = dashboard_config['slug']
        new_data['_id'] = encode_id(
            new_data['dashboard_slug'],
            data_point_name)
        return new_data

    def service_ids():
        for service_data_group in group_by('service_id', data).items():
            yield service_data_group[0], get_latest_data_points(
                service_data_group[1])

    def dashboard_configs():
        for service_id, latest_data_points in service_ids():
            dashboard_config = admin_api.get_dashboard_by_tx_id(service_id)[0]
            if dashboard_config:
                yield dashboard_config, latest_data_points

    def build_data():
        data = []
        for dashboard_config, latest_data_points in dashboard_configs():
            for data_point_name in required_data_points:
                data.append(get_stripped_down_data_for_data_point_name_only(
                    dashboard_config, latest_data_points, data_point_name))
        return data

    return build_data()

from performanceplatform.client import DataSet

from ..worker import config

import base64

from collections import OrderedDict


def group_by(keys, arr):
    groupped = OrderedDict()
    for item in arr:
        if isinstance(keys, list):
            key = tuple([item[p] for p in keys])
        else:
            key = item[keys]

        try:
            groupped[key].append(item)
        except KeyError:
            groupped[key] = [item]

    return groupped


def encode_id(*parts):
    joined = '_'.join(parts)
    joined_bytes = joined.encode('utf-8')
    return base64.urlsafe_b64encode(joined_bytes)


def _get_read_params(transform_params, latest_timestamp):
    read_params = {}
    if 'period' in transform_params:
        read_params['duration'] = 1
        read_params['period'] = transform_params['period']
    else:
        read_params['start_at'] = latest_timestamp
    read_params['sort_by'] = '_timestamp:descending'
    return read_params


def is_latest_data(data_set_config,
                   transform,
                   latest_datum,
                   additional_read_params={}):
    """
    Read from backdrop to determine if new data is the latest.
    """

    data_set = DataSet.from_group_and_type(
        config.BACKDROP_READ_URL,
        data_set_config['data_group'],
        data_set_config['data_type']
    )

    transform_params = transform.get('query_parameters', {})
    generated_read_params = _get_read_params(
        transform_params, latest_datum['_timestamp'])
    read_params = dict(
        generated_read_params.items() + additional_read_params.items())
    existing_data = data_set.get(query_parameters=read_params)

    if existing_data['data']:
        if existing_data['data'][0]['_timestamp'] > latest_datum['_timestamp']:
            return False

    return True

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

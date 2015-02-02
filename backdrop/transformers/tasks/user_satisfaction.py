from .util import encode_id
import datetime
import pytz
from dateutil import parser


def calculate_rating(datum):
    # See
    # https://github.com/alphagov/spotlight/blob/ca291ffcc86a5397003be340ec263a2466b72cfe/app/common/collections/user-satisfaction.js  # noqa
    if not datum['total:sum']:
        return None
    min_score = 1
    max_score = 5
    score = 0
    for rating in range(min_score, max_score + 1):
        rating_key = 'rating_{0}:sum'.format(rating)
        score += datum[rating_key] * rating
        # Set rating key that spotlight expects.
        datum['rating_{0}'.format(rating)] = datum[rating_key]
    mean = score / (datum['total:sum'])
    return (mean - min_score) / (max_score - min_score)


def compute(data, transform, data_set_config=None):
    # Calculate rating and set keys that spotlight expects.
    computed = []
    for datum in data:
        time_now = datetime.datetime.now(pytz.UTC)
        end_at = parser.parse(datum['_end_at']).astimezone(pytz.utc)
        # do not add record if period represented by this record
        # is not yet finished.
        if end_at < time_now:
            computed.append({
                '_id': encode_id(datum['_start_at'], datum['_end_at']),
                '_timestamp': datum['_start_at'],
                '_start_at': datum['_start_at'],
                '_end_at': datum['_end_at'],
                'rating_1': datum['rating_1:sum'],
                'rating_2': datum['rating_2:sum'],
                'rating_3': datum['rating_3:sum'],
                'rating_4': datum['rating_4:sum'],
                'rating_5': datum['rating_5:sum'],
                'num_responses': datum['total:sum'],
                'score': calculate_rating(datum),
            })
    return computed

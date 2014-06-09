from backdrop.core.timeseries import parse_period
from backdrop.core.timeutils import parse_time_as_utc
from backdrop.core.query import Query


__all__ = ['parse_query_from_request']


def parse_query_from_request(request):
    """Parses a Query object from a flask request"""
    return Query.create(**parse_request_args(request.args))


def if_present(func, value):
    """Apply the given function to the value and return if it exists"""
    if value is not None:
        return func(value)


def parse_request_args(request_args):
    args = dict()

    args['start_at'] = if_present(parse_time_as_utc,
                                  request_args.get('start_at'))

    args['end_at'] = if_present(parse_time_as_utc,
                                request_args.get('end_at'))

    args['duration'] = if_present(int, request_args.get('duration'))

    args['period'] = if_present(parse_period,
                                request_args.get('period'))

    def boolify(value):
        return {
            "true": True,
            "false": False,
        }.get(value, value)

    def parse_filter_by(filter_by):
        key, value = filter_by.split(':', 1)

        return [key, boolify(value)]

    args['filter_by'] = map(parse_filter_by, request_args.getlist('filter_by'))

    args['group_by'] = request_args.get('group_by')

    args['sort_by'] = if_present(lambda sort_by: sort_by.split(':', 1),
                                 request_args.get('sort_by'))

    args['limit'] = if_present(int, request_args.get('limit'))

    args['collect'] = []
    for collect_arg in request_args.getlist('collect'):
        if ':' in collect_arg:
            args['collect'].append(tuple(collect_arg.split(':')))
        else:
            args['collect'].append((collect_arg, 'default'))

    return args

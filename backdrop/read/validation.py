from ..core.validation import value_is_valid_datetime_string, valid, invalid


def validate_request_args(request_args):
    if 'start_at' in request_args:
        if not value_is_valid_datetime_string(request_args['start_at']):
            return invalid('start_at is not a valid datetime')
    if 'end_at' in request_args:
        if not value_is_valid_datetime_string(request_args['end_at']):
            return invalid('end_at is not a valid datetime')
    if 'filter_by' in request_args:
        if request_args['filter_by'].find(':') < 0:
            return invalid('filter_by is not valid')
        if request_args['filter_by'].startswith("$"):
            return invalid('filter_by is not valid')
    if 'period' in request_args:
        if request_args['period'] != 'week':
            return invalid('Unrecognized grouping for period')
        if "group_by" in request_args:
            if "_week_start_at" == request_args["group_by"]:
                return invalid('Cannot group on two equal keys')
    if "group_by" in request_args:
        if request_args["group_by"].startswith("_"):
            return invalid('Cannot group by internal fields')
    if 'sort' in request_args:
        if request_args['sort'].find(':') < 0:
            return invalid('sort has invalid argument')
        sort_order = request_args['sort'].split(':', 1)[1]
        if sort_order not in ['ascending', 'descending']:
            return invalid('unknown sort order')

    return valid()

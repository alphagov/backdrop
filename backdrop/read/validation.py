from ..core.validation import value_is_valid_datetime_string, valid, invalid


MESSAGES = {
    'start_at': {
        'invalid': 'start_at is not a valid datetime'
    },
    'end_at': {
        'invalid': 'end_at is not a valid datetime'
    },
    'filter_by': {
        'colon': 'filter_by must be a field name and value separated by '
                 'a colon (:) eg. authority:Westminster',
        'dollar': 'filter_by must not start with a $'
    },
    'period': {
        'invalid': 'Unrecognised grouping for period. Supported periods '
                   'include: week',
        'group': 'Cannot group on two equal keys',
        'sort': 'Period queries are sorted by time'
    },
    'group_by': {
        'internal': 'Cannot group by internal fields, internal fields start '
                    'with an underscore'
    },
    'sort_by': {
        'colon': 'sort_by must be a field name and sort direction separated '
                 'by a colon (:) eg. authority:ascending',
        'direction': 'Unrecognised sort direction. Supported directions '
                     'include: ascending, descending'
    },
    'limit': {
        'invalid': 'limit must be a positive integer'
    }
}


def validate_request_args(request_args):
    if 'start_at' in request_args:
        if not value_is_valid_datetime_string(request_args['start_at']):
            return invalid(MESSAGES['start_at']['invalid'])
    if 'end_at' in request_args:
        if not value_is_valid_datetime_string(request_args['end_at']):
            return invalid(MESSAGES['end_at']['invalid'])
    if 'filter_by' in request_args:
        if request_args['filter_by'].find(':') < 0:
            return invalid(MESSAGES['filter_by']['colon'])
        if request_args['filter_by'].startswith('$'):
            return invalid(MESSAGES['filter_by']['dollar'])
    if 'period' in request_args:
        if request_args['period'] != 'week':
            return invalid(MESSAGES['period']['invalid'])
        if 'group_by' in request_args:
            if '_week_start_at' == request_args['group_by']:
                return invalid(MESSAGES['period']['group'])
        if 'sort_by' in request_args and 'group_by' not in request_args:
            return invalid(MESSAGES['period']['sort'])
    if 'group_by' in request_args:
        if request_args['group_by'].startswith('_'):
            return invalid(MESSAGES['group_by']['internal'])
    if 'sort_by' in request_args:
        if request_args['sort_by'].find(':') < 0:
            return invalid(MESSAGES['sort_by']['colon'])
        sort_order = request_args['sort_by'].split(':', 1)[1]
        if sort_order not in ['ascending', 'descending']:
            return invalid(MESSAGES['sort_by']['direction'])
    if 'limit' in request_args:
        try:
            limit = int(request_args['limit'])
            if limit < 0:
                raise ValueError()
        except ValueError:
            return invalid(MESSAGES['limit']['invalid'])

    return valid()

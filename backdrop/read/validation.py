from ..core.validation import value_is_valid_datetime_string, valid, invalid
import re
import api

MONGO_FIELD_REGEX = re.compile(r'^[A-Za-z-_]+$')
MESSAGES = {
    "disallowed": "querying for raw data has been disallowed",
    'unrecognised': 'An unrecognised parameter was provided',
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
        'sort': 'Cannot use sort_by for period queries - period queries '
                'are always sorted by time'
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
    },
    'collect': {
        'no_grouping': 'collect is only allowed when grouping',
        'invalid': 'collect must be a valid field name',
        'internal': 'Cannot collect internal fields, internal fields start '
                    'with an underscore',
        'groupby_field': "Cannot collect by a field that is used for group_by"
    }
}


def is_a_raw_query(request_args):
    if 'group_by' in request_args:
        return False
    if 'period' in request_args:
        return False
    return True


def validate_request_args(request_args):

    if api.app.config['PREVENT_RAW_QUERIES']:
        if is_a_raw_query(request_args):
            return invalid(MESSAGES['disallowed'])

    request_args = request_args.copy()
    start_at = request_args.pop('start_at', None)
    end_at = request_args.pop('end_at', None)
    filter_by = request_args.pop('filter_by', None)
    period = request_args.pop('period', None)
    group_by = request_args.pop('group_by', None)
    sort_by = request_args.pop('sort_by', None)
    limit = request_args.pop('limit', None)
    collect = request_args.pop('collect', None)

    if len(request_args):
        return invalid(MESSAGES['unrecognised'])
    if start_at:
        if not value_is_valid_datetime_string(start_at):
            return invalid(MESSAGES['start_at']['invalid'])
    if end_at:
        if not value_is_valid_datetime_string(end_at):
            return invalid(MESSAGES['end_at']['invalid'])
    if filter_by:
        if filter_by.find(':') < 0:
            return invalid(MESSAGES['filter_by']['colon'])
        if filter_by.startswith('$'):
            return invalid(MESSAGES['filter_by']['dollar'])
    if period:
        if period != 'week':
            return invalid(MESSAGES['period']['invalid'])
        if group_by:
            if '_week_start_at' == group_by:
                return invalid(MESSAGES['period']['group'])
        if sort_by and not group_by:
            return invalid(MESSAGES['period']['sort'])
    if group_by:
        if group_by.startswith('_'):
            return invalid(MESSAGES['group_by']['internal'])
    if sort_by:
        if sort_by.find(':') < 0:
            return invalid(MESSAGES['sort_by']['colon'])
        sort_order = sort_by.split(':', 1)[1]
        if sort_order not in ['ascending', 'descending']:
            return invalid(MESSAGES['sort_by']['direction'])
    if limit:
        try:
            if int(limit) < 0:
                raise ValueError()
        except ValueError:
            return invalid(MESSAGES['limit']['invalid'])
    if collect:
        if not group_by:
            return invalid(MESSAGES['collect']['no_grouping'])
        if not MONGO_FIELD_REGEX.match(collect):
            return invalid(MESSAGES['collect']['invalid'])
        if collect.startswith('_'):
            return invalid(MESSAGES['collect']['internal'])
        if collect == group_by:
            return invalid(MESSAGES['collect']['groupby_field'])

    return valid()

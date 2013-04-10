from dateutil import parser
import api
from ..core.validation import value_is_valid_datetime_string, valid, invalid
import re

MONGO_FIELD_REGEX = re.compile(r'^[A-Za-z-_]+$')
MESSAGES = {
    "disallowed": {
        "no_grouping": "querying for raw data has been disallowed",
        "non-midnight": "start_at and end_at must be at midnight",
        "non-week-length": "difference between start_at and end_at must be 7 "
                           "days"
    },
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


def request_length_valid(start_at, end_at):
    start_at = parser.parse(start_at)
    end_at = parser.parse(end_at)
    delta = end_at - start_at
    return delta.days >= 7


def dates_on_midnight(start_at, end_at):
    start_at = parser.parse(start_at)
    end_at = parser.parse(end_at)
    return (start_at.minute + start_at.second + start_at.hour) == 0 \
        and (end_at.minute + end_at.second + end_at.hour) == 0


class Validator(object):
    def __init__(self, request_args):
        self.errors = []
        self.validate(request_args)

    def invalid(self):
        return len(self.errors) > 0

    def add_error(self, message):
        self.errors.append(invalid(message))

    def validate(self, request_args):
        raise NotImplementedError


class ParameterValidator(Validator):
    def __init__(self, request_args):
        self.allowed_parameters = set([
            'start_at',
            'end_at',
            'filter_by',
            'period',
            'group_by',
            'sort_by',
            'limit',
            'collect'
        ])
        super(ParameterValidator, self).__init__(request_args)

    def _unrecognised_parameters(self, request_args):
        return set(request_args.keys()) - self.allowed_parameters

    def validate(self, request_args):
        if len(self._unrecognised_parameters(request_args)) > 0:
            self.errors.append(invalid(
                "An unrecognised parameter was provided"))


class DatetimeValidator(Validator):
    def __init__(self, request_args, param_name):
        self.param_name = param_name
        super(DatetimeValidator, self).__init__(request_args)

    def validate(self, request_args):
        if self.param_name in request_args:
            if not value_is_valid_datetime_string(request_args[self.param_name]):
                self.errors.append(invalid('%s is not a valid datetime'
                                           % self.param_name))


class FilterByValidator(Validator):
    def validate(self, request_args):
        filter_by = request_args.get('filter_by', None)
        if filter_by:
            if filter_by.find(':') < 0:
                self.errors.append(invalid(
                    'filter_by must be a field name and value separated by '
                    'a colon (:) eg. authority:Westminster'))
            if filter_by.startswith('$'):
                self.errors.append(invalid(
                    'filter_by must not start with a $'))


def validate_request_args(request_args):

    if api.app.config['PREVENT_RAW_QUERIES']:
        if is_a_raw_query(request_args):
            return invalid(MESSAGES['disallowed']['no_grouping'])

    request_args_copy = request_args.copy()

    start_at =  request_args_copy.pop( 'start_at',  None)
    end_at =    request_args_copy.pop(   'end_at',    None)
    filter_by = request_args_copy.pop('filter_by', None)
    period =    request_args_copy.pop(   'period',    None)
    group_by =  request_args_copy.pop( 'group_by',  None)
    sort_by =   request_args_copy.pop(  'sort_by',   None)
    limit =     request_args_copy.pop(    'limit',     None)
    collect =   request_args_copy.pop(  'collect',   None)

    validators = [
        ParameterValidator(request_args),
        DatetimeValidator(request_args, 'start_at'),
        DatetimeValidator(request_args, 'end_at'),
        FilterByValidator(request_args),
    ]

    for validator in validators:
        if validator.invalid():
            return validator.errors[0]

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

    if api.app.config['PREVENT_RAW_QUERIES']:
        if start_at and end_at:
            if not request_length_valid(start_at, end_at):
                return invalid(MESSAGES['disallowed']['non-week-length'])
            if not dates_on_midnight(start_at, end_at):
                return invalid(MESSAGES['disallowed']['non-midnight'])

    return valid()


# def validate(request_args):
#     errors = [validator.validate(request_args) for validator in get_validators(request_args)]
#
#     return len(errors) > 0, errors



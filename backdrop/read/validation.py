from datetime import time
from dateutil import parser
import api
from ..core.validation import value_is_valid_datetime_string, valid, invalid
import re

MONGO_FIELD_REGEX = re.compile(r'^[A-Za-z-_]+$')


class Validator(object):
    def __init__(self, request_args, **context):
        self.errors = []
        self.validate(request_args, context)

    def invalid(self):
        return len(self.errors) > 0

    def add_error(self, message):
        self.errors.append(invalid(message))

    def validate(self, request_args, context):
        raise NotImplementedError


class MultiValueValidator(Validator):
    def param_name(self, context):
        return context.get('param_name')

    def validate_field_value(self, context):
        return context.get('validate_field_value')

    def validate(self, request_args, context):
        if self.param_name(context) in request_args:
            validate_field_value = self.validate_field_value(context)
            for value in request_args.getlist(self.param_name(context)):
                validate_field_value(value, request_args, context)


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

    def validate(self, request_args, context):
        if len(self._unrecognised_parameters(request_args)) > 0:
            self.add_error("An unrecognised parameter was provided")


class DatetimeValidator(Validator):
    def validate(self, request_args, context):
        if context['param_name'] in request_args:
            if not value_is_valid_datetime_string(
                    request_args[context['param_name']]):
                self.add_error('%s is not a valid datetime'
                               % context['param_name'])


class PositiveIntegerValidator(Validator):
    def validate(self, request_args, context):
        if context['param_name'] in request_args:
            try:
                if int(request_args[context['param_name']]) < 0:
                    raise ValueError()
            except ValueError:
                self.add_error("%s must be a positive integer"
                               % context['param_name'])


class FilterByValidator(Validator):
    def validate(self, request_args, context):
        MultiValueValidator(
            request_args,
            param_name='filter_by',
            validate_field_value=self.validate_field_value)

    def validate_field_value(self, value, request_args, context):
            if value.find(':') < 0:
                self.add_error(
                    'filter_by must be a field name and value separated by '
                    'a colon (:) eg. authority:Westminster')
            if value.startswith('$'):
                self.add_error(
                    'filter_by must not start with a $')


class ParameterMustBeThisValidator(Validator):
    def validate(self, request_args, context):
        if context['param_name'] in request_args:
            if request_args[context['param_name']] != context['must_be_this']:
                self.add_error('Unrecognised grouping for period. '
                               'Supported periods include: week')


class SortByValidator(Validator):
    def _unrecognised_direction(self, sort_by):
        return not re.match(r'^.+:(ascending|descending)$', sort_by)

    def validate(self, request_args, context):
        if 'sort_by' in request_args:
            if 'period' in request_args and 'group_by' not in request_args:
                self.add_error("Cannot sort for period queries without "
                               "group_by. Period queries are always sorted "
                               "by time.")
            if request_args['sort_by'].find(':') < 0:
                self.add_error(
                    'sort_by must be a field name and sort direction separated'
                    ' by a colon (:) eg. authority:ascending')
            if self._unrecognised_direction(request_args['sort_by']):
                self.add_error('Unrecognised sort direction. Supported '
                               'directions include: ascending, descending')


class GroupByValidator(Validator):
    def validate(self, request_args, context):
        if 'group_by' in request_args:
            if request_args['group_by'].startswith('_'):
                self.add_error('Cannot group by internal fields, '
                               'internal fields start with an underscore')


class ParamDependencyValidator(Validator):
    def validate(self, request_args, context):
        if context['param_name'] in request_args:
            if context['depends_on'] not in request_args:
                self.add_error(
                    '%s can be use only with %s'
                    % (context['param_name'], context['depends_on']))


class CollectValidator(Validator):

    def validate(self, request_args, context):
        MultiValueValidator(
            request_args,
            param_name='collect',
            validate_field_value=self.validate_field_value)

    def validate_field_value(self, value, request_args, _):
        if not MONGO_FIELD_REGEX.match(value):
            self.add_error('collect must be a valid field name')
        if value.startswith('_'):
            self.add_error('Cannot collect internal fields, '
                           'internal fields start '
                           'with an underscore')
        if value == request_args.get('group_by'):
            self.add_error("Cannot collect by a field that is "
                           "used for group_by")


class RawQueryValidator(Validator):
    def _is_a_raw_query(self, request_args):
        if 'group_by' in request_args:
            return False
        if 'period' in request_args:
            return False
        return True

    def validate(self, request_args, context):
        if self._is_a_raw_query(request_args):
            self.add_error("querying for raw data is not allowed")


def _is_valid_date(string):
    return string and value_is_valid_datetime_string(string)


class TimeSpanValidator(Validator):
    def validate(self, request_args, context):
        if self._is_valid_date_query(request_args):
            start_at = parser.parse(request_args['start_at'])
            end_at = parser.parse(request_args['end_at'])
            delta = end_at - start_at
            if delta.days < context['length']:
                self.add_error('The minimum time span for a query is 7 days')

    def _is_valid_date_query(self, request_args):
        return _is_valid_date(request_args.get('start_at')) \
            and _is_valid_date(request_args.get('end_at'))


class MidnightValidator(Validator):
    def validate(self, request_args, context):
        timestamp = request_args.get(context['param_name'])
        if _is_valid_date(timestamp):
            if parser.parse(timestamp).time() != time(0):
                self.add_error('%s must be midnight' % context['param_name'])


class MondayValidator(Validator):
    def validate(self, request_args, context):
        if 'period' in request_args:
            timestamp = request_args.get(context['param_name'])
            if _is_valid_date(timestamp):
                if (parser.parse(timestamp)).weekday() != 0:
                    self.add_error('%s must be a monday'
                                   % context['param_name'])


def validate_request_args(request_args):
    validators = [
        ParameterValidator(request_args),
        DatetimeValidator(request_args, param_name='start_at'),
        DatetimeValidator(request_args, param_name='end_at'),
        FilterByValidator(request_args),
        ParameterMustBeThisValidator(request_args, param_name='period',
                                     must_be_this='week'),
        SortByValidator(request_args),
        GroupByValidator(request_args),
        PositiveIntegerValidator(request_args, param_name='limit'),
        ParamDependencyValidator(request_args, param_name='collect',
                                 depends_on='group_by'),
        CollectValidator(request_args),
    ]

    if api.app.config['PREVENT_RAW_QUERIES']:
        validators.append(RawQueryValidator(request_args))
        validators.append(TimeSpanValidator(request_args, length=7))
        validators.append(
            MidnightValidator(request_args, param_name='start_at'))
        validators.append(MidnightValidator(request_args, param_name='end_at'))
        validators.append(MondayValidator(request_args, param_name='start_at'))
        validators.append(MondayValidator(request_args, param_name='end_at'))

    for validator in validators:
        if validator.invalid():
            return validator.errors[0]

    return valid()

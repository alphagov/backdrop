from werkzeug.routing import BaseConverter, ValidationError
from backdrop.core.validation import data_set_is_valid
from flask import request


class DataSetConverter(BaseConverter):

    def to_python(self, value):
        if not data_set_is_valid(value):
            raise ValidationError()
        return value


def generate_request_id():
    return request.headers.get('Govuk-Request-Id', '')

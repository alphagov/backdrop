from werkzeug.routing import BaseConverter, ValidationError
from backdrop.core.validation import data_set_is_valid


class DataSetConverter(BaseConverter):

    def to_python(self, value):
        if not data_set_is_valid(value):
            raise ValidationError()
        return value

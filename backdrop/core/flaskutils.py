from werkzeug.routing import BaseConverter, ValidationError
from backdrop.core.validation import bucket_is_valid


class BucketConverter(BaseConverter):
    def to_python(self, value):
        if not bucket_is_valid(value):
            raise ValidationError()
        return value

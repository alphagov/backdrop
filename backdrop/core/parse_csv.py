import csv
from backdrop.core.validation import ValidationError


def parse_csv(incoming_data):
    return list(
        validate_data(
            csv.DictReader(
                encode_as_utf8(
                    incoming_data
                )
            )
        )
    )


def validate_data(data):
    for datum in data:
        if None in datum.keys():
            raise ValidationError(
                'Some rows ins the CSV file contain more values than columns')
        if None in datum.values():
            raise ValidationError(
                'Some rows in the CSV file contain fewer values than columns')
        yield datum


def encode_as_utf8(incoming_data):
    for line in incoming_data:
        try:
            yield line.encode('utf-8')
        except UnicodeError:
            raise ValidationError("Non-UTF8 characters found.")

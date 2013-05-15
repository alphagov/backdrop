import csv
from .errors import ParseError


def parse_csv(incoming_data):
    return list(
        parse_rows(
            csv.DictReader(
                encode_as_utf8(
                    incoming_data
                )
            )
        )
    )


def parse_rows(data):
    for datum in data:
        if None in datum.keys():
            raise ParseError(
                'Some rows ins the CSV file contain more values than columns')
        if None in datum.values():
            raise ParseError(
                'Some rows in the CSV file contain fewer values than columns')
        yield datum


def encode_as_utf8(incoming_data):
    for line in incoming_data:
        try:
            yield line.encode('utf-8')
        except UnicodeError:
            raise ParseError("Non-UTF8 characters found.")

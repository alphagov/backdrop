import csv
import itertools
from ..errors import ParseError


def parse_csv(incoming_data):
    return list(
        ignore_empty_rows(
            ignore_comment_column(
                unicode_csv_reader(
                    ignore_comment_lines(lines(incoming_data)), "utf-8"
                )
            )
        )
    )


def lines(stream):
    for candidate_line in stream:
        for line in candidate_line.splitlines(True):
            yield line


def ignore_empty_rows(rows):
    return itertools.ifilterfalse(is_empty_row, rows)


def is_empty_row(row):
    return all(not v for v in row)


def ignore_comment_lines(reader):
    for line in reader:
        if not line.startswith('#'):
            yield line


def ignore_comment_column(rows):
    rows = iter(rows)
    keys = next(rows)
    index = None

    if "comment" in keys:
        index = keys.index("comment")
        keys = keys[:index] + keys[index+1:]

    yield keys

    for row in rows:
        if index is not None:
            yield row[:index] + row[index+1:]
        else:
            yield row


def unicode_csv_reader(incoming_data, encoding):
    reader = csv.reader(incoming_data)

    try:
        for row in reader:
            yield [unicode(cell, encoding) for cell in row]
    except UnicodeError:
        raise ParseError("Non-UTF8 characters found.")

import csv
from .errors import ParseError


def parse_csv(incoming_data):
    return list(
        parse_rows(
            ignore_comment_column(unicode_csv_dict_reader(
                ignore_comment_lines(lines(incoming_data)), 'utf-8')
            )
        )
    )


def lines(stream):
    for candidate_line in stream:
        for line in candidate_line.splitlines(True):
            yield line


def is_empty_row(row):
    return all(not v for v in row.values())


def parse_rows(data):
    for datum in data:
        if None in datum.keys():
            raise ParseError(
                'Some rows ins the CSV file contain more values than columns')
        if None in datum.values():
            raise ParseError(
                'Some rows in the CSV file contain fewer values than columns')
        if not is_empty_row(datum):
            yield datum


def ignore_comment_lines(reader):
    for line in reader:
        if not line.startswith('#'):
            yield line


def ignore_comment_column(data):
    for d in data:
        if "comment" in d:
            del d["comment"]
        yield d


class UnicodeCsvReader(object):
    def __init__(self, reader, encoding):
        self._reader = reader
        self._encoding = encoding

    def next(self):
        try:
            return [self._decode(cell) for cell in self._reader.next()]
        except UnicodeError:
            raise ParseError("Non-UTF8 characters found.")

    @property
    def line_num(self):
        return self._reader.line_num

    def _decode(self, cell):
        return unicode(cell, self._encoding)


def unicode_csv_dict_reader(incoming_data, encoding):
    r = csv.DictReader(incoming_data)
    r.reader = UnicodeCsvReader(r.reader, encoding)
    return r

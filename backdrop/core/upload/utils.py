from itertools import ifilter
import logging
from backdrop.core.errors import ParseError


def remove_blanks(rows):
    return filter(lambda r: not all(len(v) == 0 for v in r), rows)

def make_dicts(rows):
    """Return an iterator of dictionaries given an iterator of rows

    Given an iterator of rows consisting of a iterator of lists of values
    produces an iterator of dictionaries using the first row as the keys for
    all subsequent rows.
    """
    rows = iter(rows)
    keys = next(rows)

    for row in remove_blanks(rows):
        key_count = len(keys)
        row_count = len(row)
        if key_count < row_count:
            raise ParseError(
                'Some rows in the CSV file contain more values than columns')
        if key_count > row_count:
            raise ParseError(
                'Some rows in the CSV file contain fewer values than columns')

        yield dict(zip(keys, row))

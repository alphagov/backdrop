import xlrd
import datetime
from backdrop.core.errors import ParseError
from backdrop.core.timeutils import utc


def parse_excel(incoming_data):
    book = xlrd.open_workbook(file_contents=incoming_data.read())
    sheet = book.sheet_by_index(0)

    keys = _extract_values(sheet.row(0), book)
    data = []
    for i in range(1, sheet.nrows):
        row = zip(keys, _extract_values(sheet.row(i), book))

        data.append(dict(row))

    return data


def _extract_values(row, book):
    return [_extract_cell_value(cell, book) for cell in row]


def _extract_cell_value(cell, book):
    if cell.ctype == 3:
        time_tuple = xlrd.xldate_as_tuple(cell.value, book.datemode)
        return utc(datetime.datetime(*time_tuple))
    elif cell.ctype == 5:
        raise ParseError("Error encountered in cell")
    return cell.value

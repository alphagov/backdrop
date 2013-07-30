import xlrd
import datetime
from backdrop.core.errors import ParseError
from backdrop.core.timeutils import utc


def parse_excel(incoming_data):
    return list(_parse_excel_sheet(incoming_data))


def _parse_excel_sheet(incoming_data):
    book = xlrd.open_workbook(file_contents=incoming_data.read())
    sheet = book.sheet_by_index(0)

    for i in range(sheet.nrows):
        yield _extract_values(sheet.row(i), book)


def _extract_values(row, book):
    return [_extract_cell_value(cell, book) for cell in row]


def _extract_cell_value(cell, book):
    if cell.ctype == xlrd.XL_CELL_DATE:
        time_tuple = xlrd.xldate_as_tuple(cell.value, book.datemode)
        return utc(datetime.datetime(*time_tuple))
    elif cell.ctype == xlrd.XL_CELL_ERROR:
        raise ParseError("Error encountered in cell")
    return cell.value

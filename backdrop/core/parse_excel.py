import xlrd


def parse_excel(incoming_data):
    book = xlrd.open_workbook(file_contents=incoming_data.read())
    sheet = book.sheet_by_index(0)

    keys = _extract_values(sheet.row(0))
    data = []
    for i in range(1, sheet.nrows):
        row = zip(keys, _extract_values(sheet.row(i)))

        data.append(dict(row))

    return data


def _extract_values(row):
    return [cell.value for cell in row]
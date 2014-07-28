import unittest
from hamcrest import assert_that, contains, instance_of

from backdrop.core.upload.parse_excel import parse_excel, EXCEL_ERROR
from tests.support.test_helpers import fixture_path


class ParseExcelTestCase(unittest.TestCase):
    def _parse_excel(self, file_name):
        file_stream = open(fixture_path(file_name))
        return parse_excel(file_stream)

    def test_parse_an_xlsx_file(self):
        assert_that(self._parse_excel("data.xlsx"), contains(contains(
            ["name", "age", "nationality"],
            ["Pawel", 27, "Polish"],
            ["Max", 35, "Italian"],
        )))

    def test_parse_xlsx_dates(self):
        assert_that(self._parse_excel("dates.xlsx"), contains(contains(
            ["date"],
            ["2013-12-03T13:30:00+00:00"],
            ["2013-12-04T00:00:00+00:00"],
        )))

    def test_parse_xls_file(self):
        assert_that(self._parse_excel("xlsfile.xls"), contains(contains(
            ["date", "name", "number"],
            ["2013-12-03T13:30:00+00:00", "test1", 12],
            ["2013-12-04T00:00:00+00:00", "test2", 34],
        )))

    def test_parse_xlsx_with_error(self):
        assert_that(self._parse_excel("error.xlsx"), contains(contains(
            ["date", "name", "number", "error"],
            ["2013-12-03T13:30:00+00:00", "test1", 12, EXCEL_ERROR],
            ["2013-12-04T00:00:00+00:00", "test2", 34, EXCEL_ERROR],
        )))

    def test_parse_xlsx_with_multiple_sheets(self):
        assert_that(self._parse_excel("multiple_sheets.xlsx"), contains(
            contains(
                ["Sheet 1 content"],
                ["Nothing exciting"]
            ),
            contains(
                ["Sheet 2 content", None],
                ["Sheet Name", "Sheet Index"],
                ["First", 0],
                ["Second", 1]
            )))

    def test_parse_xlsx_handle_empty_cells_and_lines(self):
        assert_that(self._parse_excel("empty_cell_and_row.xlsx"), contains(
            contains(
                ["Next cell is none", None, "Previous cell is none"],
                [None, None, None],
                ["The above row", "is full", "of nones"]
            )))

    def test_that_numbers_are_converted_to_int_where_possible(self):
        data = map(list, self._parse_excel("xlsfile.xls"))

        assert_that(data[0][1][2], instance_of(int))

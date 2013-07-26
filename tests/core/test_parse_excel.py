import os
import unittest
from hamcrest import assert_that, only_contains

from backdrop.core.parse_excel import parse_excel

class ParseExcelTestCase(unittest.TestCase):
    def test_parse_an_xlsx_file(self):
        file_stream = open(_fixture_path("data.xlsx"))
        data = parse_excel(file_stream)

        assert_that(data,
                    only_contains(
                        {"name": "Pawel", "age": 27, "nationality": "Polish"},
                        {"name": "Max", "age": 35, "nationality": "Italian"}))


def _fixture_path(name):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'features', 'fixtures', name))
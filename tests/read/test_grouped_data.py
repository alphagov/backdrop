import unittest
from hamcrest import *
from backdrop.read.response import GroupedData


class TestWeeklyGroupedData(unittest.TestCase):
    def test_adding_documents(self):
        stub_document = {"_count": 0}
        data = GroupedData()
        data.add(stub_document)
        assert_that(data.data(), has_length(1))

    def test_returned_data_should_be_immutable(self):
        stub_document = {"_count": 0}
        data = GroupedData()
        data.add(stub_document)
        another_data = data.data()
        try:
            another_data.append({"even_more_nonsense": True})
            assert_that(False, "expected an exception")
        except AttributeError as e:
            assert_that(str(e), "'tuple' object has no attribute append")

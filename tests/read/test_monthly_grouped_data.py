import unittest
from hamcrest import *
from backdrop.read.response import create_period_group_month
from tests.support.test_helpers import d


class MonthlyGroupedData(object):
    def __init__(self, cursor):
        self._data = []
        for doc in cursor:
            self.__add(doc)

    def __add(self, doc):
        datum = {}
        datum.update({
            "values": [create_period_group_month(subgroup) for
                       subgroup in doc["_subgroup"]]})
        self._data.append(datum)

    def data(self):
        return tuple(self._data)


class TestMonthlyGroupedData(unittest.TestCase):
    def test_adding_mongo_document(self):
        stub_document = {"_subgroup": []}
        data = MonthlyGroupedData([stub_document])
        assert_that(data.data(), has_length(1))

    def test_month_start_at_gets_expanded_into_start_and_end_fields(self):
        stub_document = {
            "_subgroup": [{
                "_month_start_at": d(2013, 4, 1),
                "_count": 1
            }]}
        data = MonthlyGroupedData([stub_document])
        values = data.data()[0]['values']
        assert_that(values, has_length(1))

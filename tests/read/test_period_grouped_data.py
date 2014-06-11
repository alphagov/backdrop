from nose.tools import *
from hamcrest import *
from backdrop.core.timeseries import MONTH
from backdrop.core.response import PeriodGroupedData
from tests.support.test_helpers import d


class TestPeriodGroupedData(object):
    def test_filled_data_without_collect(self):
        stub_document = {
            "_subgroup": [{
                "_month_start_at": d(2013, 9, 1),
                "_count": 1
            }]
        }
        stub_collect = None

        data = PeriodGroupedData([stub_document], MONTH)
        data.fill_missing_periods(d(2013, 7, 1), d(2013, 10, 1), stub_collect)
        values = data.data()[0]["values"]

        assert_that(values, has_length(3))

    def test_filled_data_with_collect(self):
        stub_document = {
            "_subgroup": [{
                "_month_start_at": d(2013, 9, 1),
                "_count": 1
            }]
        }
        stub_collect = [('volume', 'sum')]

        data = PeriodGroupedData([stub_document], MONTH)
        data.fill_missing_periods(d(2013, 7, 1), d(2013, 10, 1), stub_collect)
        values = data.data()[0]["values"]

        assert_that(values, has_length(3))
        assert_that(values, has_item(has_entry('volume:sum', None)))

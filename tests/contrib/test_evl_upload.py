import unittest
from hamcrest import assert_that, is_
from backdrop.contrib.evl_upload import service_volumetrics


class EVLServiceVolumetrics(unittest.TestCase):

    def test_converts_evl_volumetrics_data_to_normalised_data(self):
        def ignore_rows(rows):
            return [["Ignored"] for _ in range(rows)]

        evl_volumetrics_raw_data = \
            ignore_rows(2) + \
            [["Date", "30/07/2013"]] + \
            ignore_rows(21) + \
            [["TTS.02", "- Relicense", 52]] + \
            [["TTS.03", "- SORN", 13]] + \
            ignore_rows(39)

        data = [row for row in service_volumetrics(evl_volumetrics_raw_data)]

        assert_that(data, is_([["_timestamp", "timeSpan", "successful_tax_disc", "successful_sorn"],
                               ["30/07/2013", "day", 52, 13]]))

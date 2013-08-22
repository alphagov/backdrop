from datetime import timedelta
import unittest
from hamcrest import assert_that, is_
from backdrop.contrib.evl_upload_filters import service_volumetrics, service_failures, channel_volumetrics, customer_satisfaction
from tests.support.test_helpers import d_tz


class EVLServiceVolumetrics(unittest.TestCase):

    def ignore_rows(self, rows):
        return [["Ignored"] for _ in range(rows)]

    def test_converts_service_volumetrics_data_to_normalised_data(self):
        timestamp = d_tz(2013, 7, 30)
        evl_volumetrics_raw_data = \
            self.ignore_rows(2) + \
            [["Date", timestamp]] + \
            self.ignore_rows(21) + \
            [["TTS.02", "- Relicense", 52]] + \
            [["TTS.03", "- SORN", 13]] + \
            self.ignore_rows(39)

        data = list(service_volumetrics(evl_volumetrics_raw_data))

        assert_that(data, is_([["_timestamp", "_id", "timeSpan", "successful_tax_disc", "successful_sorn"],
                               [timestamp, "2013-07-30", "day", 52, 13]]))

    def test_converts_service_failures_data_to_normalised_data(self):
        timestamp = d_tz(2013, 7, 30)
        failures_raw_data = [
            ["First sheet to be ignored"],
            self.ignore_rows(1) +
            [["Date", timestamp]] +
            self.ignore_rows(4) +
            [["Failure 1", 0, 10, 0, 2]] +
            [["Failure 2", 1, 20, 0, 3]] +
            [["Failure 3", 2, 30, 0, 4]] +
            [["", "Blank first column means end of failures list"]]
        ]

        data = list(service_failures(failures_raw_data))

        assert_that(data, is_([
            ["_timestamp", "_id", "type", "reason", "count", "description"],
            [timestamp, "2013-07-30.tax-disc.0", "tax-disc", 0, 10, "Failure 1"],
            [timestamp, "2013-07-30.sorn.0",     "sorn",     0, 2,  "Failure 1"],
            [timestamp, "2013-07-30.tax-disc.1", "tax-disc", 1, 20, "Failure 2"],
            [timestamp, "2013-07-30.sorn.1",     "sorn",     1, 3,  "Failure 2"],
            [timestamp, "2013-07-30.tax-disc.2", "tax-disc", 2, 30, "Failure 3"],
            [timestamp, "2013-07-30.sorn.2",     "sorn",     2, 4,  "Failure 3"]
        ]))

    def test_converts_missing_failure_as_zero(self):
        timestamp = d_tz(2013, 7, 30)
        failures_raw_data = [
            ["First sheet to be ignored"],
            self.ignore_rows(1) +
            [["Date", timestamp]] +
            self.ignore_rows(4) +
            [["No tax-disc failure", 0, '', 0, 2]] +
            [["No sorn failure", 1, 20, 0, '']] +
            [["", "Blank first column means end of failures list"]]
        ]

        data = list(service_failures(failures_raw_data))

        assert_that(data, is_([
            ["_timestamp", "_id", "type", "reason", "count", "description"],
            [timestamp, "2013-07-30.tax-disc.0", "tax-disc", 0, 0,  "No tax-disc failure"],
            [timestamp, "2013-07-30.sorn.0",     "sorn",     0, 2,  "No tax-disc failure"],
            [timestamp, "2013-07-30.tax-disc.1", "tax-disc", 1, 20, "No sorn failure"],
            [timestamp, "2013-07-30.sorn.1",     "sorn",     1, 0,  "No sorn failure"],
        ]))

    def test_converts_channel_volumetrics_raw_data_to_normalised_data(self):
        monday = d_tz(2013, 7, 29)
        tuesday = monday + timedelta(days=1)
        wednesday = monday + timedelta(days=2)
        volumetrics_raw_data = \
            self.ignore_rows(1) + \
            [["Channel", monday, tuesday, wednesday, "", "", "", ""]] + \
            [["Agent successful", 10, 20, '']] + \
            [["IVR successful", 30, 40, '']] + \
            [["WEB successful", 40, 50, '']] + \
            [["Total successful all channels", 40, 50, 0]] + \
            self.ignore_rows(17)

        data = list(channel_volumetrics(volumetrics_raw_data))

        assert_that(data, is_([["_timestamp", "_id", "successful_agent", "successful_ivr", "successful_web"],
                               [monday, "2013-07-29", 10, 30, 40],
                               [tuesday, "2013-07-30", 20, 40, 50]]))

    def test_converts_customer_satisfaction_raw_data_to_normalised_data(self):
        may = d_tz(2013, 5, 1)
        june = d_tz(2013, 6, 1)
        july = d_tz(2013, 7, 1)
        raw_data = \
            self.ignore_rows(4) + \
            [[may, 0.1, 0.2],
             [june, 0.3, 0.4],
             [july, 0.5, 0.6],
             ["Total Result", 1, 2]]

        data = list(customer_satisfaction(raw_data))

        assert_that(data, is_([["_timestamp", "_id", "satisfaction_tax_disc", "satisfaction_sorn"],
                               ["2013-05-01T00:00:00+00:00", "2013-05-01", 0.1, 0.2],
                               ["2013-06-01T00:00:00+00:00", "2013-06-01", 0.3, 0.4],
                               ["2013-07-01T00:00:00+00:00", "2013-07-01", 0.5, 0.6]]))

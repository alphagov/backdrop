from itertools import ifilter
from pprint import pprint
import re
import unittest
from hamcrest import *
from datetime import datetime
from backdrop.core.timeutils import as_utc


def extract_column_header(sheet):
    HEADER_INDEX = 3
    return sheet[HEADER_INDEX]


def extract_transaction_rows(sheet):
    TRANSACTION_INDEXES = {
           4: ["Assisted Digital", "Relicensing"],
           5: ["Assisted Digital", "Relicensing"],
           7: ["Assisted Digital", "SORN"],
           10: ["Fully Digital", "Relicensing"],
           11: ["Fully Digital", "Relicensing"],
           12: ["Fully Digital", "Relicensing"],
           13: ["Fully Digital", "Relicensing"],
           15: ["Fully Digital", "SORN"],
           16: ["Fully Digital", "SORN"],
           17: ["Fully Digital", "SORN"],
           18: ["Fully Digital", "SORN"],
           21: ["Manual", "Relicensing"],
           22: ["Manual", "Relicensing"],
           23: ["Manual", "Relicensing"],
           25: ["Manual", "SORN"],
           26: ["Manual", "SORN"],
           27: ["Manual", "SORN"],
           28: ["Manual", "SORN"],
           29: ["Manual", "SORN"],
           30: ["Manual", "SORN"],
           31: ["Manual", "SORN"],
    }

    def transaction_row(index):
        channel_service = TRANSACTION_INDEXES[index]
        return channel_service + sheet[index][2:4]

    return extract_column_header(sheet), map(transaction_row, TRANSACTION_INDEXES.keys())


def create_transaction_data(header, row):
    CHANNEL_INDEX = 0
    SERVICE_INDEX = 1
    TRANSACTION_NAME_INDEX = 2
    DATES_START_INDEX = 3
    SERVICES = {
        "Relicensing": "tax-disc",
        "SORN": "sorn"
    }

    volumes = zip(header, row)[DATES_START_INDEX:]

    def transaction_data(date_volume):
        date, volume = date_volume
        date = as_utc(datetime.strptime(date, "%b %Y"))
        service = SERVICES[row[SERVICE_INDEX]]
        channel = row[CHANNEL_INDEX].lower().replace(" ", "-")
        transaction = row[TRANSACTION_NAME_INDEX]

        return [date.isoformat(), service, channel, transaction, volume]

    return map(transaction_data, volumes)


def remove_summary_columns(sheet):
    DATES_START_INDEX = 3
    DATE_REGEXP = re.compile("[A-Z][a-z]{2}\s\d{4}")

    header = extract_column_header(sheet)

    def add_date_index(mem, i):
        if bool(DATE_REGEXP.match(header[i])):
            mem.append(i)
            return mem
        else:
            return mem

    date_indexes = reduce(add_date_index, range(DATES_START_INDEX,len(header)), [])

    def remove_columns_from_row(row):
        return row[:DATES_START_INDEX] + [row[i] for i in date_indexes]


    return map(remove_columns_from_row, sheet)



class TestEVLVolumetrics(unittest.TestCase):

    def test_extracts_transaction_rows_from_sheet(self):
        sheet = [
           ["Ignore"],
           ["Ignore"],
           ["Ignore"],
           ["Channel Descriptions", "", "Transaction", "Apr 2012"],
           ["Assisted Digital", "Relicensing", "V-V10 Licence Application Post Office", 1000],
           ["", "", "V-V11 Licence Renewal Reminder Post Office", 1001],
           ["Ignore"],
           ["", "SORN", "V-V11 Some transaction", 1003],
           ["Ignore"],
           ["Ignore"],
           ["Fully Digital", "Relicensing", "V-V10 Licence Application EVL", 1006],
           ["", "", "V-V11 Fleets", 1007],
           ["", "", "V-V11 Licence Renewal Reminder EVL", 1008],
           ["", "", "V-V85 and V85/1 HGV Licence Application EVL", 1009],
           ["Ignore"],
           ["", "SORN", "V-V11 SORN EVL", 1011],
           ["", "", "V-V85/1 HGV SORN Declaration EVL", 1012],
           ["", "", "V-V890 SORN Declaration EVL", 1013],
           ["", "", "V-V890 SORN Declaration Fleets", 1014],
           ["Ignore"],
           ["Ignore"],
           ["Manual", "Relicensing", "V-V890 Another transaction", 1017],
           ["", "", "V-V11 Licence Renewal Reminder Local Office", 1018],
           ["", "", "V-V85 and V85/1 HGV Licence Application", 1019],
           ["Ignore"],
           ["", "SORN", "V-V11 SORN Local Office", 1021],
           ["", "", "V-V85/1 HGV SORN Declaration", 1022],
           ["", "", "V-V890 SORN Declaration", 1023],
           ["", "", "V-V890 SORN Declaration Key from Image", 1024],
           ["", "", "V-V890 SORN Declaration Refunds Input", 1025],
           ["", "", "V-V890 SORN Declaration Vehicles Input", 1026],
           ["", "", "V-V890 SORN Declaration Vehicles Triage", 1027],
           ["Ignore"],
           ["Ignore"],
           ["Ignore"]
        ]


        header, rows = extract_transaction_rows(sheet)
        assert_that(header, is_(["Channel Descriptions", "", "Transaction", "Apr 2012"]))
        assert_that(rows, is_not(has_item(["Ignore"])))
        assert_that(rows, has_items(
           ["Assisted Digital", "Relicensing", "V-V10 Licence Application Post Office", 1000],
           ["Assisted Digital", "Relicensing", "V-V11 Licence Renewal Reminder Post Office", 1001],
           ["Assisted Digital", "SORN", "V-V11 Some transaction", 1003],
           ["Fully Digital", "Relicensing", "V-V10 Licence Application EVL", 1006],
           ["Fully Digital", "Relicensing", "V-V11 Fleets", 1007],
           ["Fully Digital", "Relicensing", "V-V11 Licence Renewal Reminder EVL", 1008],
           ["Fully Digital", "Relicensing", "V-V85 and V85/1 HGV Licence Application EVL", 1009],
           ["Fully Digital", "SORN", "V-V11 SORN EVL", 1011],
           ["Fully Digital", "SORN", "V-V85/1 HGV SORN Declaration EVL", 1012],
           ["Fully Digital", "SORN", "V-V890 SORN Declaration EVL", 1013],
           ["Fully Digital", "SORN", "V-V890 SORN Declaration Fleets", 1014],
           ["Manual", "Relicensing", "V-V890 Another transaction", 1017],
           ["Manual", "Relicensing", "V-V11 Licence Renewal Reminder Local Office", 1018],
           ["Manual", "Relicensing", "V-V85 and V85/1 HGV Licence Application", 1019],
           ["Manual", "SORN", "V-V11 SORN Local Office", 1021],
           ["Manual", "SORN", "V-V85/1 HGV SORN Declaration", 1022],
           ["Manual", "SORN", "V-V890 SORN Declaration", 1023],
           ["Manual", "SORN", "V-V890 SORN Declaration Key from Image", 1024],
           ["Manual", "SORN", "V-V890 SORN Declaration Refunds Input", 1025],
           ["Manual", "SORN", "V-V890 SORN Declaration Vehicles Input", 1026],
           ["Manual", "SORN", "V-V890 SORN Declaration Vehicles Triage", 1027]
        ))

    def test_removes_summary_columns(self):
        sheet = [
           ["_", "_", "_", "_", "_", "_"],
           ["_", "_", "_", "_", "_", "_"],
           ["_", "_", "_", "_", "_", "_"],
           ["Channel Descriptions", "", "Transaction", "Apr 2012", "2012/13 Total", "Mar 2013"],
           ["Assisted Digital", "Relicensing", "V-V10 Licence Application Post Office", 1000, 2000, 3000],
           ["", "", "V-V11 Licence Renewal Reminder Post Office", 1001, 2001, 3001,],
           ["_", "_", "_", "_", "_", "_"],
           ["", "SORN", "V-V11 Some transaction", 1003, 2003, 3003],
           ["_", "_", "_", "_", "_", "_"],
           ["_", "_", "_", "_", "_", "_"],
           ["Fully Digital", "Relicensing", "V-V10 Licence Application EVL", 1006, 2006, 3006],
           ["", "", "V-V11 Fleets", 1007, 2007, 3007],
           ["", "", "V-V11 Licence Renewal Reminder EVL", 1008, 2008, 3008],
           ["", "", "V-V85 and V85/1 HGV Licence Application EVL", 1009, 2008, 3008],
           ["_", "_", "_", "_", "_", "_"],
           ["", "SORN", "V-V11 SORN EVL", 1011, 2011, 3011],
           ["", "", "V-V85/1 HGV SORN Declaration EVL", 1012, 2012, 3012],
           ["", "", "V-V890 SORN Declaration EVL", 1013, 2013, 3013],
           ["", "", "V-V890 SORN Declaration Fleets", 1014, 2014, 3014],
           ["_", "_", "_", "_", "_", "_"],
           ["_", "_", "_", "_", "_", "_"],
           ["Manual", "Relicensing", "V-V890 Another transaction", 1017, 2017, 3017],
           ["", "", "V-V11 Licence Renewal Reminder Local Office", 1018, 2018, 3018],
           ["", "", "V-V85 and V85/1 HGV Licence Application", 1019, 2019, 3019],
           ["_", "_", "_", "_", "_", "_"],
           ["", "SORN", "V-V11 SORN Local Office", 1021, 2021, 3021],
           ["", "", "V-V85/1 HGV SORN Declaration", 1022, 2022, 3022],
           ["", "", "V-V890 SORN Declaration", 1023, 2023, 3023],
           ["", "", "V-V890 SORN Declaration Key from Image", 1024, 2024, 3024],
           ["", "", "V-V890 SORN Declaration Refunds Input", 1025, 2025, 3025],
           ["", "", "V-V890 SORN Declaration Vehicles Input", 1026, 2026, 3026],
           ["", "", "V-V890 SORN Declaration Vehicles Triage", 1027, 2027, 3027],
           ["_", "_", "_", "_", "_", "_"],
           ["_", "_", "_", "_", "_", "_"],
           ["_", "_", "_", "_", "_", "_"],
        ]

        assert_that(remove_summary_columns(sheet), has_items(
            ["Channel Descriptions", "", "Transaction", "Apr 2012", "Mar 2013"],
            ["", "", "V-V85 and V85/1 HGV Licence Application EVL", 1009, 3008],
        ))


    def test_creating_transaction_data_from_row_and_header(self):
        header = ["Channel Descriptions", "", "Transaction", "Apr 2012", "Mar 2013", "May 2013"]
        row = ["Manual", "Relicensing", "V-V890 Another transaction", 1, 2, 3]

        assert_that(create_transaction_data(header, row), has_items(
            ["2012-04-01T00:00:00+00:00", "tax-disc", "manual", "V-V890 Another transaction", 1],
            ["2013-03-01T00:00:00+00:00", "tax-disc", "manual", "V-V890 Another transaction", 2],
            ["2013-05-01T00:00:00+00:00", "tax-disc", "manual", "V-V890 Another transaction", 3],
        ))

    def test_creating_transaction_data_from_row_and_header_maps_channel_and_services(self):
        header = ["Channel Descriptions", "", "Transaction", "Apr 2012"]
        row = ["Fully Digital", "SORN", "V-V11 SORN EVL", 10]

        assert_that(create_transaction_data(header, row), has_items(
            ["2012-04-01T00:00:00+00:00", "sorn", "fully-digital", "V-V11 SORN EVL", 10],
        ))
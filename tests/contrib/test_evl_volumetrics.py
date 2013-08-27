import unittest

from hamcrest import *

from backdrop.contrib.evl_volumetrics import extract_transaction_rows, create_transaction_data, remove_summary_columns


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
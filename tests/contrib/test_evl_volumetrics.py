import unittest
from hamcrest import *


def extract_transaction_rows(sheet):
    TRANSACTION_INDEXES = {
        "header": 3,
        "V-V10 Licence Application Post Office": 4,
        "V-V11 Licence Renewal Reminder Post Office": 5,
        "V-V11 Some transaction": 7,
        "V-V10 Licence Application EVL": 10,
        "V-V11 Fleets": 11,
        "V-V11 Licence Renewal Reminder EVL": 12,
        "V-V85 and V85/1 HGV Licence Application EVL": 13,
        "V-V11 SORN EVL": 15,
        "V-V85/1 HGV SORN Declaration EVL": 16,
        "V-V890 SORN Declaration EVL": 17,
        "V-V890 SORN Declaration Fleets": 18,
        "V-V890 Another transaction": 21,
        "V-V11 Licence Renewal Reminder Local Office": 22,
        "V-V85 and V85/1 HGV Licence Application": 23,
        "V-V11 SORN Local Office": 25,
        "V-V85/1 HGV SORN Declaration": 26,
        "V-V890 SORN Declaration": 27,
        "V-V890 SORN Declaration Key from Image": 28,
        "V-V890 SORN Declaration Refunds Input": 29,
        "V-V890 SORN Declaration Vehicles Input": 30,
        "V-V890 SORN Declaration Vehicles Triage": 31
    }
    return map(lambda i: sheet[i], TRANSACTION_INDEXES.values())


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


        assert_that(extract_transaction_rows(sheet), is_not(has_item(["Ignore"])))
        assert_that(extract_transaction_rows(sheet), has_items(
           ["Channel Descriptions", "", "Transaction", "Apr 2012"],
           ["Assisted Digital", "Relicensing", "V-V10 Licence Application Post Office", 1000],
           ["", "", "V-V11 Licence Renewal Reminder Post Office", 1001],
           ["", "SORN", "V-V11 Some transaction", 1003],
           ["Fully Digital", "Relicensing", "V-V10 Licence Application EVL", 1006],
           ["", "", "V-V11 Fleets", 1007],
           ["", "", "V-V11 Licence Renewal Reminder EVL", 1008],
           ["", "", "V-V85 and V85/1 HGV Licence Application EVL", 1009],
           ["", "SORN", "V-V11 SORN EVL", 1011],
           ["", "", "V-V85/1 HGV SORN Declaration EVL", 1012],
           ["", "", "V-V890 SORN Declaration EVL", 1013],
           ["", "", "V-V890 SORN Declaration Fleets", 1014],
           ["Manual", "Relicensing", "V-V890 Another transaction", 1017],
           ["", "", "V-V11 Licence Renewal Reminder Local Office", 1018],
           ["", "", "V-V85 and V85/1 HGV Licence Application", 1019],
           ["", "SORN", "V-V11 SORN Local Office", 1021],
           ["", "", "V-V85/1 HGV SORN Declaration", 1022],
           ["", "", "V-V890 SORN Declaration", 1023],
           ["", "", "V-V890 SORN Declaration Key from Image", 1024],
           ["", "", "V-V890 SORN Declaration Refunds Input", 1025],
           ["", "", "V-V890 SORN Declaration Vehicles Input", 1026],
           ["", "", "V-V890 SORN Declaration Vehicles Triage", 1027]
        ))
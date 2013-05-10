import csv


def parse_csv(csv_stream):
    return csv.DictReader(csv_stream)

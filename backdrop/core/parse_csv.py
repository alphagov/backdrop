import csv


def parse_csv(csv_stream):
    return list(csv.DictReader(csv_stream))

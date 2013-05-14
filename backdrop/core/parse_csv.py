import csv


def parse_csv(csv_stream):
    return list(csv.DictReader(encode_as_utf8(csv_stream)))


def encode_as_utf8(incoming_data):
    for line in incoming_data:
        yield line.encode('utf-8')

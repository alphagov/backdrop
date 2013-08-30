from datetime import datetime
import re
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
        return channel_service + sheet[index][2:]

    return extract_column_header(sheet), map(transaction_row,
                                             TRANSACTION_INDEXES.keys())


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
        if volume == "" or volume == "-":
            volume = 0
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

    date_indexes = reduce(add_date_index,
                          range(DATES_START_INDEX, len(header)), [])

    def remove_columns_from_row(row):
        return row[:DATES_START_INDEX] + [row[i] for i in date_indexes]

    return map(remove_columns_from_row, sheet)

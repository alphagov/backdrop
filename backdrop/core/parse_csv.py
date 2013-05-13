import csv


class MoreValuesThanColumnsException(Exception):
    pass


class MissingValuesForSomeColumnsException(Exception):
    pass


class DictReader(csv.DictReader):
    def next(self):
        next_item = csv.DictReader.next(self)
        if None in next_item.keys():
            raise MoreValuesThanColumnsException()
        if None in next_item.values():
            raise MissingValuesForSomeColumnsException()
        return next_item


def parse_csv(csv_stream):
    return DictReader(csv_stream)

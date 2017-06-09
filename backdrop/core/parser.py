import StringIO
import csv
import itertools


def json_to_csv(data):
    if not isinstance(data, (list, tuple)):
        return ""

    string = StringIO.StringIO()
    out = csv.writer(string)

    header = set(itertools.chain.from_iterable(i.keys() for i in data))
    header = sorted(list(header))

    parsed = []
    for item in data:
        if not item:
            continue
        if not parsed:
            parsed = [header]
        parsed.append([item.get(i, "") for i in header])

    out.writerows(parsed)
    return string.getvalue()

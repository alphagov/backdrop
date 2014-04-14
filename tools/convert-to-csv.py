#!/usr/bin/env python
# encoding: utf-8

"""
Rough and ready conversion script to turn our JSON output into CSV.

Note that this only works on "flat" data like, such as what you get from a raw
query in backdrop. It can't handle nesting, like when you've used a group_by
query.
"""

import json
import csv
import sys


def main(filename):
    with open(filename, 'r') as f, open('out.csv', 'w') as g:
        data = json.loads(f.read())

        field_names = set()
        for row in data['data']:
            field_names.update(set(row.keys()))

        csv_writer = csv.DictWriter(
            g,
            fieldnames=sorted(field_names),
            delimiter=',')
        csv_writer.writeheader()

        for row in data['data']:
            csv_writer.writerow(row)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("Usage: {} <file.json>".format(sys.argv[0]))
        sys.exit(2)

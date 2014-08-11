from contextlib import contextmanager
import json
from nose.tools import assert_equal
from os.path import dirname, join as pjoin

from backdrop.core.data_set import flatten_data
from backdrop.core.query import Query
from backdrop.core.timeseries import Week
from tests.support.test_helpers import d_tz


@contextmanager
def fixture(name):
    filename = pjoin(dirname(__file__), '..', 'fixtures', name)
    with open(filename, 'r') as f:
        yield json.loads(f.read())


def test_flatten_data():
    query = Query.create(
        end_at=d_tz(2014, 8, 8, 0, 0, 0),
        period=Week(),
        duration=3,
        group_by=['department', 'deviceCategory'],
        collect=[('pageviews', 'sum')],
        flatten=True,
    )

    with fixture('pre_flattened_response.json') as response:
        flat_data = flatten_data(response['data'], query)

        assert_equal(
            flat_data[:10],
            [
                {
                    '_end_at': '2014-07-21T00:00:00+00:00',
                    '_start_at': '2014-07-14T00:00:00+00:00',
                    'attorney-generals-office:desktop:pageviews:sum': 7459.0
                },
                {
                    '_end_at': '2014-07-28T00:00:00+00:00',
                    '_start_at': '2014-07-21T00:00:00+00:00',
                    'attorney-generals-office:desktop:pageviews:sum': 3421.0
                },
                {
                    '_end_at': '2014-08-04T00:00:00+00:00',
                    '_start_at': '2014-07-28T00:00:00+00:00',
                    'attorney-generals-office:desktop:pageviews:sum': 3179.0
                },
                {
                    '_end_at': '2014-07-21T00:00:00+00:00',
                    '_start_at': '2014-07-14T00:00:00+00:00',
                    'attorney-generals-office:mobile:pageviews:sum': 1446.0
                },
                {
                    '_end_at': '2014-07-28T00:00:00+00:00',
                    '_start_at': '2014-07-21T00:00:00+00:00',
                    'attorney-generals-office:mobile:pageviews:sum': 650.0
                },
                {
                    '_end_at': '2014-08-04T00:00:00+00:00',
                    '_start_at': '2014-07-28T00:00:00+00:00',
                    'attorney-generals-office:mobile:pageviews:sum': 774.0
                },
                {
                    '_end_at': '2014-07-21T00:00:00+00:00',
                    '_start_at': '2014-07-14T00:00:00+00:00',
                    'attorney-generals-office:tablet:pageviews:sum': 1346.0
                },
                {
                    '_end_at': '2014-07-28T00:00:00+00:00',
                    '_start_at': '2014-07-21T00:00:00+00:00',
                    'attorney-generals-office:tablet:pageviews:sum': 515.0
                },
                {
                    '_end_at': '2014-08-04T00:00:00+00:00',
                    '_start_at': '2014-07-28T00:00:00+00:00',
                    'attorney-generals-office:tablet:pageviews:sum': 512.0
                },
                {
                    '_end_at': '2014-07-21T00:00:00+00:00',
                    '_start_at': '2014-07-14T00:00:00+00:00',
                    'cabinet-office:desktop:pageviews:sum': 99224.0
                },
            ]
        )


def test_flatten_data():
    query = Query.create(
        end_at=d_tz(2014, 8, 8, 0, 0, 0),
        period=Week(),
        duration=3,
        collect=[('pageviews', 'sum')],
        flatten=True,
    )

    with fixture('pre_flattened_response_no_values.json') as response:
        flat_data = flatten_data(response['data'], query)

        assert_equal(
            flat_data,
            [
                {
                    '_end_at': '2014-07-21T00:00:00+00:00',
                    '_start_at': '2014-07-14T00:00:00+00:00',
                    'pageviews:sum': 5000897.0
                },
                {
                    '_end_at': '2014-07-28T00:00:00+00:00',
                    '_start_at': '2014-07-21T00:00:00+00:00',
                    'pageviews:sum': 4488161.0
                },
                {
                    '_end_at': '2014-08-04T00:00:00+00:00',
                    '_start_at': '2014-07-28T00:00:00+00:00',
                    'pageviews:sum': 4428801.0
                },
            ]
        )

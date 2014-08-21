from datetime import datetime
import json
from nose.tools import assert_equal
import pytz

from backdrop.core.data_set import build_data
from backdrop.core.query import Query
from backdrop.core.timeseries import Week
from tests.support.test_helpers import d_tz, json_fixture


def test_build_data_with_flatten():
    query = Query.create(
        end_at=d_tz(2014, 8, 8, 0, 0, 0),
        period=Week(),
        duration=3,
        group_by=['department', 'deviceCategory'],
        collect=[('pageviews', 'sum')],
        flatten=True,
    )

    with json_fixture('build_data_results_to_flatten.json', parse_dates=True) as result:
        flat_data = build_data(result, query)
        assert_equal(
            flat_data.data(),
            (
                {
                    '_count': 3.0,
                    '_start_at': datetime(2014, 7, 14, tzinfo=pytz.utc),
                    '_end_at': datetime(2014, 7, 21, tzinfo=pytz.utc),
                    'attorney-generals-office:desktop:pageviews:sum': 611.0,
                    'attorney-generals-office:mobile:pageviews:sum': 634.0,
                    'attorney-generals-office:tablet:pageviews:sum': 609.0,
                    'cabinet-office:desktop:pageviews:sum': 601.0,
                    'cabinet-office:mobile:pageviews:sum': 623.0,
                    'cabinet-office:tablet:pageviews:sum': 611.0,
                    'department-for-business-innovation-skills:desktop:pageviews:sum': 634.0,
                    'department-for-business-innovation-skills:mobile:pageviews:sum': 609.0,
                    'department-for-business-innovation-skills:tablet:pageviews:sum': 601.0
                },
                {
                    '_count': 3.0,
                    '_start_at': datetime(2014, 7, 21, tzinfo=pytz.utc),
                    '_end_at': datetime(2014, 7, 28, tzinfo=pytz.utc),
                    'attorney-generals-office:desktop:pageviews:sum': 623.0,
                    'attorney-generals-office:mobile:pageviews:sum': 633.0,
                    'attorney-generals-office:tablet:pageviews:sum': 610.0,
                    'cabinet-office:desktop:pageviews:sum': 602.0,
                    'cabinet-office:mobile:pageviews:sum': 646.0,
                    'cabinet-office:tablet:pageviews:sum': 623.0,
                    'department-for-business-innovation-skills:desktop:pageviews:sum': 633.0,
                    'department-for-business-innovation-skills:mobile:pageviews:sum': 610.0,
                    'department-for-business-innovation-skills:tablet:pageviews:sum': 602.0
                },
                {
                    '_count': 3.0,
                    '_start_at': datetime(2014, 7, 28, tzinfo=pytz.utc),
                    '_end_at': datetime(2014, 8, 4, tzinfo=pytz.utc),
                    'attorney-generals-office:desktop:pageviews:sum': 622.0,
                    'attorney-generals-office:mobile:pageviews:sum': 645.0,
                    'attorney-generals-office:tablet:pageviews:sum': 621.0,
                    'cabinet-office:desktop:pageviews:sum': 603.0,
                    'cabinet-office:mobile:pageviews:sum': 669.0,
                    'cabinet-office:tablet:pageviews:sum': 622.0,
                    'department-for-business-innovation-skills:desktop:pageviews:sum': 645.0,
                    'department-for-business-innovation-skills:mobile:pageviews:sum': 621.0,
                    'department-for-business-innovation-skills:tablet:pageviews:sum': 603.0
                }
            )
        )

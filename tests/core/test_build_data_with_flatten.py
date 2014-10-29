from datetime import datetime
import json
from nose.tools import assert_true
import pytz

from backdrop.core.data_set import build_data
from backdrop.core.query import Query
from backdrop.core.timeseries import Week
from tests.support.test_helpers import d_tz, json_fixture


class TestBuildDataWithFlatten(object):
    def test_build_data_with_flatten(self):
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
            assert_true(all(item in flat_data.data() for item in
                            (
                            {
                                '_count': 3.0,
                                '_end_at': datetime(2014, 7, 21, tzinfo=pytz.utc),
                                '_start_at': datetime(2014, 7, 14, tzinfo=pytz.utc),
                                'department': 'attorney-generals-office',
                                'deviceCategory': 'desktop',
                                'pageviews:sum': 611.0,
                            },
                            {
                                '_count': 3.0,
                                '_end_at': datetime(2014, 7, 21, tzinfo=pytz.utc),
                                '_start_at': datetime(2014, 7, 14, tzinfo=pytz.utc),
                                'department': 'attorney-generals-office',
                                'deviceCategory': 'mobile',
                                'pageviews:sum': 634.0,
                            },
                            {
                                '_count': 3.0,
                                '_end_at': datetime(2014, 7, 21, tzinfo=pytz.utc),
                                '_start_at': datetime(2014, 7, 14, tzinfo=pytz.utc),
                                'department': 'attorney-generals-office',
                                'deviceCategory': 'tablet',
                                'pageviews:sum': 609.0,
                            },
                            {
                                '_count': 3.0,
                                '_end_at': datetime(2014, 7, 21, tzinfo=pytz.utc),
                                '_start_at': datetime(2014, 7, 14, tzinfo=pytz.utc),
                                'department': 'cabinet-office',
                                'deviceCategory': 'desktop',
                                'pageviews:sum': 601.0,
                            },
                            {
                                '_count': 3.0,
                                '_end_at': datetime(2014, 7, 21, tzinfo=pytz.utc),
                                '_start_at': datetime(2014, 7, 14, tzinfo=pytz.utc),
                                'department': 'cabinet-office',
                                'deviceCategory': 'mobile',
                                'pageviews:sum': 623.0,
                            },
                            {
                                '_count': 3.0,
                                '_end_at': datetime(2014, 7, 21, tzinfo=pytz.utc),
                                '_start_at': datetime(2014, 7, 14, tzinfo=pytz.utc),
                                'department': 'cabinet-office',
                                'deviceCategory': 'tablet',
                                'pageviews:sum': 611.0,
                            },
                            {
                                '_count': 3.0,
                                '_end_at': datetime(2014, 7, 21, tzinfo=pytz.utc),
                                '_start_at': datetime(2014, 7, 14, tzinfo=pytz.utc),
                                'department': 'department-for-business-innovation-skills',
                                'deviceCategory': 'desktop',
                                'pageviews:sum': 634.0,
                            },
                            {
                                '_count': 3.0,
                                '_end_at': datetime(2014, 7, 21, tzinfo=pytz.utc),
                                '_start_at': datetime(2014, 7, 14, tzinfo=pytz.utc),
                                'department': 'department-for-business-innovation-skills',
                                'deviceCategory': 'mobile',
                                'pageviews:sum': 609.0,
                            },
                            {
                                '_count': 3.0,
                                '_end_at': datetime(2014, 7, 21, tzinfo=pytz.utc),
                                '_start_at': datetime(2014, 7, 14, tzinfo=pytz.utc),
                                'department': 'department-for-business-innovation-skills',
                                'deviceCategory': 'tablet',
                                'pageviews:sum': 601.0,
                            },
                            {
                                '_count': 3.0,
                                '_end_at': datetime(2014, 7, 28, tzinfo=pytz.utc),
                                '_start_at': datetime(2014, 7, 21, tzinfo=pytz.utc),
                                'department': 'attorney-generals-office',
                                'deviceCategory': 'desktop',
                                'pageviews:sum': 623.0,
                            }
                            )
                            ))

import unittest
import urllib
import datetime
from hamcrest import *
from mock import patch, Mock
import pytz
from backdrop.core.timeseries import WEEK
from backdrop.read import api
from backdrop.read.query import Query
from tests.support.bucket import setup_bucket
from tests.support.test_helpers import has_status, has_header


class NoneData(object):
    def data(self):
        return None


class QueryingApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()

    @setup_bucket("foo", service="some-service", data_type="some-type")
    @patch('backdrop.core.bucket.Bucket.query')
    def test_period_query_is_executed(self, mock_query):
        mock_query.return_value = NoneData()
        self.app.get('/data/some-service/some-type?period=week')
        mock_query.assert_called_with(
            Query.create(period=WEEK))

    @setup_bucket("foo", service="some-service", data_type="some-type", raw_queries_allowed=True)
    @patch('backdrop.core.bucket.Bucket.query')
    def test_filter_by_query_is_executed(self, mock_query):
        mock_query.return_value = NoneData()
        self.app.get('/data/some-service/some-type?filter_by=zombies:yes')
        mock_query.assert_called_with(
            Query.create(filter_by=[[u'zombies', u'yes']]))

    @setup_bucket("foo", service="some-service", data_type="some-type")
    @patch('backdrop.core.bucket.Bucket.query')
    def test_group_by_query_is_executed(self, mock_query):
        mock_query.return_value = NoneData()
        self.app.get('/data/some-service/some-type?group_by=zombies')
        mock_query.assert_called_with(
            Query.create(group_by=u'zombies'))

    @setup_bucket("foo", service="some-service", data_type="some-type", raw_queries_allowed=True)
    @patch('backdrop.core.bucket.Bucket.query')
    def test_query_with_start_and_end_is_executed(self, mock_query):
        mock_query.return_value = NoneData()
        expected_start_at = datetime.datetime(2012, 12, 5, 8, 12, 43,
                                              tzinfo=pytz.UTC)
        expected_end_at = datetime.datetime(2012, 12, 12, 8, 12, 43,
                                            tzinfo=pytz.UTC)
        self.app.get(
            '/data/some-service/some-type?start_at=' +
            urllib.quote("2012-12-05T08:12:43+00:00") +
            '&end_at=' + urllib.quote("2012-12-12T08:12:43+00:00")
        )
        mock_query.assert_called_with(
            Query.create(start_at=expected_start_at, end_at=expected_end_at))

    @setup_bucket("foo", service="some-service", data_type="some-type")
    @patch('backdrop.core.bucket.Bucket.query')
    def test_group_by_with_period_is_executed(self, mock_query):
        mock_query.return_value = NoneData()
        self.app.get(
            '/data/some-service/some-type?period=week&group_by=stuff'
        )
        mock_query.assert_called_with(
            Query.create(period=WEEK, group_by="stuff"))

    @setup_bucket("foo", service="some-service", data_type="some-type", raw_queries_allowed=True)
    @patch('backdrop.core.bucket.Bucket.query')
    def test_sort_query_is_executed(self, mock_query):
        mock_query.return_value = NoneData()
        self.app.get(
            '/data/some-service/some-type?sort_by=value:ascending'
        )
        mock_query.assert_called_with(
            Query.create(sort_by=["value", "ascending"]))

        self.app.get(
            '/data/some-service/some-type?sort_by=value:descending'
        )
        mock_query.assert_called_with(
            Query.create(sort_by=["value", "descending"]))

    @setup_bucket("bucket", service="some-service", data_type="some-type", queryable=False)
    def test_returns_404_when_bucket_is_not_queryable(self):
        response = self.app.get('/data/some-service/some-type')
        assert_that(response, has_status(404))


class PreflightChecksApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()

    @setup_bucket("bucket", service="some-service", data_type="some-type")
    def test_cors_preflight_requests_have_empty_body(self):
        response = self.app.open('/data/some-service/some-type', method='OPTIONS')
        assert_that(response.status_code, is_(200))
        assert_that(response.data, is_(""))

    @setup_bucket("bucket", service="some-service", data_type="some-type")
    def test_cors_preflight_are_allowed_from_all_origins(self):
        response = self.app.open('/data/some-service/some-type', method='OPTIONS')
        assert_that(response, has_header('Access-Control-Allow-Origin', '*'))

    @setup_bucket("bucket", service="some-service", data_type="some-type")
    def test_cors_preflight_result_cache(self):
        response = self.app.open('/data/some-service/some-type', method='OPTIONS')
        assert_that(response, has_header('Access-Control-Max-Age', '86400'))

    @setup_bucket("bucket", service="some-service", data_type="some-type")
    def test_cors_requests_can_cache_control(self):
        response = self.app.open('/data/some-service/some-type', method='OPTIONS')
        assert_that(response, has_header('Access-Control-Allow-Headers', 'cache-control'))

    @setup_bucket("bucket", service="some-service", data_type="some-type")
    def test_max_age_is_30_min_for_non_realtime_buckets(self):
        response = self.app.get('/data/some-service/some-type?period=week')

        assert_that(response, has_header('Cache-Control', 'max-age=1800, must-revalidate'))

    @setup_bucket("bucket", service="some-service", data_type="some-type", realtime=True)
    def test_max_age_is_2_min_for_realtime_buckets(self):
        response = self.app.get('/data/some-service/some-type?period=week')

        assert_that(response, has_header('Cache-Control', 'max-age=120, must-revalidate'))

import unittest
import urllib
import datetime
from hamcrest import *
from mock import patch, Mock
import pytz
from backdrop.read import api
from backdrop.read.query import Query


class NoneData(object):
    def data(self):
        return None


class ReadApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()

    @patch('backdrop.core.bucket.Bucket.query')
    def test_period_query_is_executed(self, mock_query):
        mock_query.return_value = NoneData()
        self.app.get('/foo?period=week')
        mock_query.assert_called_with(
            Query.create(period=u"week"))

    @patch('backdrop.core.bucket.Bucket.query')
    def test_filter_by_query_is_executed(self, mock_query):
        mock_query.return_value = NoneData()
        self.app.get('/foo?filter_by=zombies:yes')
        mock_query.assert_called_with(
            Query.create(filter_by=[[u'zombies', u'yes']]))

    @patch('backdrop.core.bucket.Bucket.query')
    def test_group_by_query_is_executed(self, mock_query):
        mock_query.return_value = NoneData()
        self.app.get('/foo?group_by=zombies')
        mock_query.assert_called_with(
            Query.create(group_by=u'zombies'))

    @patch('backdrop.core.bucket.Bucket.query')
    def test_period_query_is_executed(self, mock_query):
        mock_query.return_value = NoneData()
        expected_start_at = datetime.datetime(2012, 12, 5, 8, 12, 43,
                                              tzinfo=pytz.UTC)
        expected_end_at = datetime.datetime(2012, 12, 12, 8, 12, 43,
                                            tzinfo=pytz.UTC)
        self.app.get(
            '/foo?start_at=' + urllib.quote("2012-12-05T08:12:43+00:00") +
            '&end_at=' + urllib.quote("2012-12-12T08:12:43+00:00")
        )
        mock_query.assert_called_with(
            Query.create(start_at=expected_start_at, end_at=expected_end_at))

    @patch('backdrop.core.bucket.Bucket.query')
    def test_group_by_with_period_is_executed(self, mock_query):
        mock_query.return_value = NoneData()
        self.app.get(
            '/foo?period=week&group_by=stuff'
        )
        mock_query.assert_called_with(
            Query.create(period="week", group_by="stuff"))

    @patch('backdrop.core.bucket.Bucket.query')
    def test_sort_query_is_executed(self, mock_query):
        mock_query.return_value = NoneData()
        self.app.get(
            '/foo?sort_by=value:ascending'
        )
        mock_query.assert_called_with(
            Query.create(sort_by=["value", "ascending"]))

        self.app.get(
            '/foo?sort_by=value:descending'
        )
        mock_query.assert_called_with(
            Query.create(sort_by=["value", "descending"]))

    def test_cors_preflight_requests_have_empty_body(self):
        response = self.app.open('/bucket', method='OPTIONS')
        assert_that(response.status_code, is_(200))
        assert_that(response.data, is_(""))

    def test_cors_preflight_are_allowed_from_all_origins(self):
        response = self.app.open('/bucket', method='OPTIONS')
        assert_that(response.headers['Access-Control-Allow-Origin'], is_('*'))

    def test_cors_preflight_result_cache(self):
        response = self.app.open('/bucket', method='OPTIONS')
        assert_that(response.headers['Access-Control-Max-Age'],
                    is_('86400'))

    def test_cors_requests_can_cache_control(self):
        response = self.app.open('/bucket', method='OPTIONS')
        assert_that(response.headers['Access-Control-Allow-Headers'],
                    is_('cache-control'))

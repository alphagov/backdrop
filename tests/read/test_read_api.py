import unittest
import urllib
import datetime
from hamcrest import *
from mock import patch
import pytz
from backdrop.read import api


class ReadApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = api.app.test_client()

    @patch('backdrop.core.storage.Bucket.query')
    def test_period_query_is_executed(self, mock_query):
        mock_query.return_value = None
        self.app.get('/foo?period=week')
        mock_query.assert_called_with(period=u"week")

    @patch('backdrop.core.storage.Bucket.query')
    def test_filter_by_query_is_executed(self, mock_query):
        mock_query.return_value = None
        self.app.get('/foo?filter_by=zombies:yes')
        mock_query.assert_called_with(filter_by=[[u'zombies', u'yes']])

    @patch('backdrop.core.storage.Bucket.query')
    def test_group_by_query_is_executed(self, mock_query):
        mock_query.return_value = None
        self.app.get('/foo?group_by=zombies')
        mock_query.assert_called_with(group_by=u'zombies')

    @patch('backdrop.core.storage.Bucket.query')
    def test_start_at_is_executed(self, mock_query):
        mock_query.return_value = None
        expected_start_at = datetime.datetime(2012, 12, 12, 8, 12, 43,
                                              tzinfo=pytz.UTC)
        self.app.get(
            '/foo?start_at=' + urllib.quote("2012-12-12T08:12:43+00:00")
        )
        mock_query.assert_called_with(start_at=expected_start_at)

    @patch('backdrop.core.storage.Bucket.query')
    def test_start_at_is_executed(self, mock_query):
        mock_query.return_value = None
        expected_end_at = datetime.datetime(2012, 12, 12, 8, 12, 43,
                                            tzinfo=pytz.UTC)
        self.app.get(
            '/foo?end_at=' + urllib.quote("2012-12-12T08:12:43+00:00")
        )
        mock_query.assert_called_with(end_at=expected_end_at)
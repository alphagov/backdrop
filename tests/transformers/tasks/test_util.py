import unittest
from freezegun import freeze_time

from hamcrest import assert_that, is_
from mock import patch, Mock

from backdrop.transformers.tasks.util import(
    encode_id,
    group_by,
    is_latest_data)


class UtilTestCase(unittest.TestCase):
    def test_encode_id(self):
        assert_that(
            encode_id('foo', 'bar'),
            is_('Zm9vX2Jhcg==')
        )

    def test_group_by(self):
        groupped_data = group_by(['a', 'b'], [
            {
                'a': 'foo',
                'b': 'bar',
            },
            {
                'a': 'foo',
                'b': 'bar',
            },
            {
                'a': 'foo',
                'b': 'foo',
            },
        ])

        assert_that(len(groupped_data.keys()), is_(2))
        assert_that(len(groupped_data[('foo', 'bar')]), is_(2))
        assert_that(len(groupped_data[('foo', 'foo')]), is_(1))

    @freeze_time('2018, 1, 09 00:00:00')
    @patch("performanceplatform.client.DataSet.from_group_and_type")
    def test_is_latest_data(self, mock_dataset):
        mockdata = Mock()
        mockdata.get.return_value = {
            'data': [
                {
                    '_count': 1.0,
                    '_end_at': '2012-01-19T00:00:00+00:00',
                    '_timestamp': '2012-01-12T00:00:00+00:00'
                }
            ]
        }
        mock_dataset.return_value = mockdata
        is_actually_latest_data = is_latest_data(
            {
                'data_group': 'transactions-explorer',
                'data_type': 'spreadsheet'
            },
            {
                'output': {
                    'data-group': 'transactions-explorer',
                    'data-type': 'spreadsheet'
                }
            },
            {
                "_timestamp": "2013-04-01T00:00:00+00:00"
            },
            {
                'filter_by': 'dashboard_slug:sorn'
            }
        )
        mockdata.get.assert_called_once_with(query_parameters={
            'filter_by': 'dashboard_slug:sorn',
            'start_at': u'2013-04-01T00:00:00+00:00',
            'end_at': '2018-01-09T00:00:00+00:00',
            'sort_by': '_timestamp:descending'})
        assert_that(is_actually_latest_data, is_(True))

    @freeze_time('2018, 1, 09 00:00:00')
    @patch("performanceplatform.client.DataSet.from_group_and_type")
    def test_is_latest_data_is_false(self, mock_dataset):
        mockdata = Mock()
        mockdata.get.return_value = {
            'data': [
                {
                    '_count': 1.0,
                    '_end_at': '2012-01-19T00:00:00+00:00',
                    '_timestamp': '2018-01-12T00:00:00+00:00'
                }
            ]
        }
        mock_dataset.return_value = mockdata
        is_actually_latest_data = is_latest_data(
            {
                'data_group': 'transactions-explorer',
                'data_type': 'spreadsheet'
            },
            {
                'output': {
                    'data-group': 'transactions-explorer',
                    'data-type': 'spreadsheet'
                }
            },
            {
                "_timestamp": "2013-04-01T00:00:00+00:00"
            },
            {
                'filter_by': 'dashboard_slug:sorn'
            }
        )
        mockdata.get.assert_called_once_with(query_parameters={
            'filter_by': 'dashboard_slug:sorn',
            'start_at': u'2013-04-01T00:00:00+00:00',
            'end_at': '2018-01-09T00:00:00+00:00',
            'sort_by': '_timestamp:descending'})
        assert_that(is_actually_latest_data, is_(False))

    @patch("performanceplatform.client.DataSet.from_group_and_type")
    def test_is_latest_data_when_transform_has_period(self, mock_dataset):
        mockdata = Mock()
        mockdata.get.return_value = {
            'data': [
                {
                    '_count': 1.0,
                    '_end_at': '2012-01-19T00:00:00+00:00',
                    '_timestamp': '2012-01-12T00:00:00+00:00'
                }
            ]
        }
        mock_dataset.return_value = mockdata
        is_actually_latest_data = is_latest_data(
            {
                'data_group': 'transactions-explorer',
                'data_type': 'spreadsheet'
            },
            {
                'output': {
                    'data-group': 'transactions-explorer',
                    'data-type': 'spreadsheet'
                },
                'query_parameters': {
                    'period': 'year'
                }
            },
            {
                "_timestamp": "2013-04-01T00:00:00+00:00"
            },
            {
                'filter_by': 'dashboard_slug:sorn'
            }
        )
        mockdata.get.assert_called_once_with(query_parameters={
            'duration': 1,
            'filter_by': 'dashboard_slug:sorn',
            'period': 'year',
            'sort_by': '_timestamp:descending'})
        assert_that(is_actually_latest_data, is_(True))

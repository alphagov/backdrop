import unittest

from hamcrest import assert_that, is_, contains_inanyorder, equal_to

from backdrop.transformers.tasks.latest_transaction_explorer_values import(
    compute)
from backdrop.transformers.tasks.util import(
    encode_id)

from mock import patch, Mock, call

import json
import os

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__),
    '../'
    'fixtures')
with open(os.path.join(
        FIXTURE_PATH,
        'transactions_explorer_example_data.json'), 'r') as f:
    data = json.loads(f.read())

data_to_post = [
    {
        "_id": encode_id('sorn', 'cost_per_transaction'),
        "_timestamp": "2013-04-01T00:00:00+00:00",
        "cost_per_transaction": 5.2,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('sorn', 'digital_cost_per_transaction'),
        "_timestamp": "2013-04-01T00:00:00+00:00",
        "digital_cost_per_transaction": 2.52,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        # It looks like this id generation is correct.
        # The latest data point transform takes the data_type
        # as the second argument. In the case of digital_takeup
        # the data_type is digital_takeup.
        "_id": encode_id('sorn', 'digital_takeup'),
        "_timestamp": "2013-04-01T00:00:00+00:00",
        "digital_takeup": 0.965537995968002,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('sorn', 'number_of_digital_transactions'),
        "_timestamp": "2013-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_digital_transactions": 2184914,
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('sorn', 'number_of_transactions'),
        "_timestamp": "2013-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_transactions": 2262898,
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('sorn', 'total_cost'),
        "_timestamp": "2013-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "total_cost": 11767069.6,
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('bis-returns', 'cost_per_transaction'),
        "_timestamp": "2013-04-01T00:00:00+00:00",
        "cost_per_transaction": 5.2,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('bis-returns', 'digital_cost_per_transaction'),
        "_timestamp": "2013-04-01T00:00:00+00:00",
        "digital_cost_per_transaction": 2.52,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('bis-returns', 'digital_takeup'),
        "_timestamp": "2013-04-01T00:00:00+00:00",
        "digital_takeup": 0.965537995968002,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('bis-returns', 'number_of_digital_transactions'),
        "_timestamp": "2013-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_digital_transactions": 2184914,
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('bis-returns', 'number_of_transactions'),
        "_timestamp": "2013-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_transactions": 2262898,
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('bis-returns', 'total_cost'),
        "_timestamp": "2013-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "total_cost": 11767069.6,
        "type": "seasonally-adjusted"
    }
]


class ComputeTestCase(unittest.TestCase):

    @patch("performanceplatform.client.DataSet.from_group_and_type")
    @patch("performanceplatform.client.AdminAPI.get_dashboard_by_tx_id")
    def test_compute(self, mock_dashboard_finder, mock_dataset):
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

        sorn_dashboard_config = [{
            'slug': 'sorn'
        }]

        bis_returns_dashboard_config = [{
            'slug': 'bis-returns'
        }]

        mock_dashboard_finder.side_effect = lambda x: {
            'bis-annual-returns': bis_returns_dashboard_config,
            'sorn-innit': sorn_dashboard_config
        }.get(x, [])
        transformed_data = compute(data, {'output': {
            'data-group': 'transactions-explorer',
            'data-type': 'spreadsheet'}})

        calls = [call(query_parameters={
            'filter_by': 'dashboard_slug:bis-returns',
            'start_at': u'2013-04-01T00:00:00+00:00',
            'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:bis-returns',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:bis-returns',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:bis-returns',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:bis-returns',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:bis-returns',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:sorn',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:sorn',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:sorn',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:sorn',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:sorn',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:sorn',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'})]
        mockdata.get.has_calls(calls)
        assert_that(transformed_data, contains_inanyorder(*data_to_post))
        assert_that(len(transformed_data), is_(12))

    @patch("performanceplatform.client.DataSet.from_group_and_type")
    @patch("performanceplatform.client.AdminAPI.get_dashboard_by_tx_id")
    def test_compute_when_no_new_data(
            self,
            mock_dashboard_finder,
            mock_dataset):
        mockdata = Mock()
        mockdata.get.return_value = {
            'data': [
                {
                    '_count': 1.0,
                    '_end_at': '2018-01-19T00:00:00+00:00',
                    '_timestamp': '2018-01-12T00:00:00+00:00'
                }
            ]
        }
        mock_dataset.return_value = mockdata

        sorn_dashboard_config = [{
            'slug': 'sorn'
        }]

        bis_returns_dashboard_config = [{
            'slug': 'bis-returns'
        }]

        mock_dashboard_finder.side_effect = lambda x: {
            'bis-annual-returns': bis_returns_dashboard_config,
            'sorn-innit': sorn_dashboard_config
        }.get(x, [])
        transformed_data = compute(data, {'output': {
            'data-group': 'transactions-explorer',
            'data-type': 'spreadsheet'}})

        calls = [call(query_parameters={
            'filter_by': 'dashboard_slug:bis-returns',
            'start_at': u'2013-04-01T00:00:00+00:00',
            'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:bis-returns',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:bis-returns',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:bis-returns',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:bis-returns',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:bis-returns',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:sorn',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:sorn',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:sorn',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:sorn',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:sorn',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'}),
            call(query_parameters={
                'filter_by': 'dashboard_slug:sorn',
                'start_at': u'2013-04-01T00:00:00+00:00',
                'sort_by': '_timestamp:descending'})]
        mockdata.get.has_calls(calls)

        assert_that(transformed_data, equal_to([]))
        assert_that(len(transformed_data), is_(0))

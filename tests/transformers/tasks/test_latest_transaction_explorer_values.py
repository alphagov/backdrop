import unittest

from hamcrest import assert_that, is_, contains_inanyorder

from backdrop.transformers.tasks.latest_transaction_explorer_values import(
    compute)
from backdrop.transformers.tasks.util import(
    encode_id)

from mock import patch

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
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "cost_per_transaction": 5.2,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('sorn', 'digital_cost_per_transaction'),
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "digital_cost_per_transaction": 2.52,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('sorn', 'digital_takeup'),
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "digital_takeup": 0.965537995968002,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('sorn', 'number_of_digital_transactions'),
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_digital_transactions": 2184914,
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('sorn', 'number_of_transactions'),
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_transactions": 2262898,
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('sorn', 'total_cost'),
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "total_cost": 11767069.6,
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('bis-returns', 'cost_per_transaction'),
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "cost_per_transaction": 5.2,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('bis-returns', 'digital_cost_per_transaction'),
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "digital_cost_per_transaction": 2.52,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('bis-returns', 'digital_takeup'),
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "digital_takeup": 0.965537995968002,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('bis-returns', 'number_of_digital_transactions'),
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_digital_transactions": 2184914,
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('bis-returns', 'number_of_transactions'),
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_transactions": 2262898,
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": encode_id('bis-returns', 'total_cost'),
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "total_cost": 11767069.6,
        "type": "seasonally-adjusted"
    }
]


class ComputeTestCase(unittest.TestCase):

    @patch("performanceplatform.client.AdminAPI.get_dashboard_by_tx_id")
    def test_compute(self, mock_dashboard_finder):
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
        # data is only data added to tx so we may need to make our own request.
        # this should include the digital-takeup if not present.
        # if it is should re overwrite for ease/if newer?.
        transformed_data = compute(data, {})

        assert_that(transformed_data, contains_inanyorder(*data_to_post))
        assert_that(len(transformed_data), is_(12))

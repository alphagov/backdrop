import base64
import unittest

from hamcrest import assert_that, is_, equal_to

from backdrop.transformers.tasks.latest_transaction_explorer_values import(
    compute)

from mock import patch


bis_annual_returns_data = [
    {
        "_day_start_at": "2011-04-01T00:00:00+00:00",
        "_hour_start_at": "2011-04-01T00:00:00+00:00",
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_month_start_at": "2011-04-01T00:00:00+00:00",
        "_quarter_start_at": "2011-04-01T00:00:00+00:00",
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "_updated_at": "2014-03-19T10:44:32.286000+00:00",
        "_week_start_at": "2011-03-28T00:00:00+00:00",
        "cost_per_transaction": 5.2,
        "digital_cost_per_transaction": 2.52,
        "digital_takeup": 0.965537995968002,
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_digital_transactions": 2184914,
        "number_of_transactions": 2262898,
        "period": "year",
        "service_id": "bis-annual-returns",
        "total_cost": 11767069.6,
        "type": "seasonally-adjusted"
    },
    {
        "_day_start_at": "2012-01-01T00:00:00+00:00",
        "_hour_start_at": "2012-01-01T00:00:00+00:00",
        "_id": "MjAxMi0wMS0wMSAwMDowMDowMDIwMTMtMDEtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_month_start_at": "2012-01-01T00:00:00+00:00",
        "_quarter_start_at": "2012-01-01T00:00:00+00:00",
        "_timestamp": "2012-01-01T00:00:00+00:00",
        "_updated_at": "2014-03-19T10:44:32.287000+00:00",
        "_week_start_at": "2011-12-26T00:00:00+00:00",
        "cost_per_transaction": 2.63,
        "digital_cost_per_transaction": 2.36,
        "digital_takeup": 0.9756123825537215,
        "end_at": "2013-01-01T00:00:00+00:00",
        "number_of_digital_transactions": 2301214,
        "number_of_transactions": 2358738,
        "period": "year",
        "service_id": "bis-annual-returns",
        "total_cost": 6203480.9399999995,
        "type": "seasonally-adjusted"
    }
]

sorn_data = [
    {
        "_day_start_at": "2011-04-01T00:00:00+00:00",
        "_hour_start_at": "2011-04-01T00:00:00+00:00",
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_month_start_at": "2011-04-01T00:00:00+00:00",
        "_quarter_start_at": "2011-04-01T00:00:00+00:00",
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "_updated_at": "2014-03-19T10:44:32.286000+00:00",
        "_week_start_at": "2011-03-28T00:00:00+00:00",
        "cost_per_transaction": 5.2,
        "digital_cost_per_transaction": 2.52,
        "digital_takeup": 0.965537995968002,
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_digital_transactions": 2184914,
        "number_of_transactions": 2262898,
        "period": "year",
        "service_id": "sorn-innit",
        "total_cost": 11767069.6,
        "type": "seasonally-adjusted"
    },
    {
        "_day_start_at": "2012-01-01T00:00:00+00:00",
        "_hour_start_at": "2012-01-01T00:00:00+00:00",
        "_id": "MjAxMi0wMS0wMSAwMDowMDowMDIwMTMtMDEtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_month_start_at": "2012-01-01T00:00:00+00:00",
        "_quarter_start_at": "2012-01-01T00:00:00+00:00",
        "_timestamp": "2012-01-01T00:00:00+00:00",
        "_updated_at": "2014-03-19T10:44:32.287000+00:00",
        "_week_start_at": "2011-12-26T00:00:00+00:00",
        "cost_per_transaction": 2.63,
        "digital_cost_per_transaction": 2.36,
        "digital_takeup": 0.9756123825537215,
        "end_at": "2013-01-01T00:00:00+00:00",
        "number_of_digital_transactions": 2301214,
        "number_of_transactions": 2358738,
        "period": "year",
        "service_id": "sorn-innit",
        "total_cost": 6203480.9399999995,
        "type": "seasonally-adjusted"
    }
]

data = sorn_data + bis_annual_returns_data

sorn_dashboard_config = [{
    'slug': 'sorn'
}]

bis_returns_dashboard_config = [{
    'slug': 'bis-returns'
}]

data_to_post = [
    {
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "cost_per_transaction": 5.2,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "digital_cost_per_transaction": 2.52,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "digital_takeup": 0.965537995968002,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_digital_transactions": 2184914,
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_transactions": 2262898,
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "type": "seasonally-adjusted"
    },
    {
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "sorn-innit",
        "dashboard_slug": "sorn",
        "total_cost": 11767069.6,
        "type": "seasonally-adjusted"
    },
    {
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "cost_per_transaction": 5.2,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "digital_cost_per_transaction": 2.52,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "digital_takeup": 0.965537995968002,
        "end_at": "2012-04-01T00:00:00+00:00",
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_digital_transactions": 2184914,
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
        "_timestamp": "2011-04-01T00:00:00+00:00",
        "end_at": "2012-04-01T00:00:00+00:00",
        "number_of_transactions": 2262898,
        "period": "year",
        "service_id": "bis-annual-returns",
        "dashboard_slug": "bis-returns",
        "type": "seasonally-adjusted"
    },
    {
        "_id": "MjAxMS0wNC0wMSAwMDowMDowMDIwMTItMDQtMD"
               "EgMDA6MDA6MDBiaXMtYW5udWFsLXJldHVybnM=",
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
        #get all dashboards by tr ids
        #for each dashboard get latest data
        #for each dashboard get enough to write to write dashboard slug in https://www.preview.performance.service.gov.uk/data/service-aggregates/latest-dataset-values?flatten=true
        #new record in https://www.preview.performance.service.gov.uk/data/service-aggregates/latest-dataset-values?flatten=true - one for each latest value, this should include the digital-takeup if not present. if it is should re overwrite for ease/if newer?.
        mock_dashboard_finder.side_effect = lambda x: {
            'bis-annual-returns': bis_returns_dashboard_config,
            'sorn-innit': sorn_dashboard_config
        }.get(x, [])
        #data is only data added to tx so we may need to make our own request.
        transformed_data = compute(data, {})

        assert_that(transformed_data, equal_to(data_to_post))
        #assert_that(len(transformed_data), is_(1))
        #assert_that(
            #transformed_data[0]['_id'],
            #is_(base64.b64encode(mock_dashboard_data[0]['slug'] + 'completion_rate')))
        #assert_that(
            #transformed_data[0]['_timestamp'],
            #is_('2013-10-14T00:00:00+00:00'))
        #assert_that(
            #transformed_data[0]['completion_rate'], is_(0.29334396173774413))

import base64
import unittest

from hamcrest import assert_that, is_

from backdrop.transformers.tasks.latest_dataset_value import compute

from mock import patch


data = [
    {
        "_day_start_at": "2013-10-07T00:00:00+00:00",
        "_end_at": "2013-10-14T00:00:00+00:00",
        "_hour_start_at": "2013-10-07T00:00:00+00:00",
        "_id": "MjAxMy0xMC0wN1QwMDowMDowMCswMDowMF8yMDEzLTEwLTE0VDAwOjAwOjAwKzAwOjAw",
        "_month_start_at": "2013-10-01T00:00:00+00:00",
        "_quarter_start_at": "2013-10-01T00:00:00+00:00",
        "_start_at": "2013-10-07T00:00:00+00:00",
        "_timestamp": "2013-10-07T00:00:00+00:00",
        "_updated_at": "2015-01-14T12:51:45.621000+00:00",
        "_week_start_at": "2013-10-07T00:00:00+00:00",
        "_year_start_at": "2013-01-01T00:00:00+00:00",
        "rate": 0.26958105646630237
    },
    {
        "_day_start_at": "2013-10-14T00:00:00+00:00",
        "_end_at": "2013-10-21T00:00:00+00:00",
        "_hour_start_at": "2013-10-14T00:00:00+00:00",
        "_id": "MjAxMy0xMC0xNFQwMDowMDowMCswMDowMF8yMDEzLTEwLTIxVDAwOjAwOjAwKzAwOjAw",
        "_month_start_at": "2013-10-01T00:00:00+00:00",
        "_quarter_start_at": "2013-10-01T00:00:00+00:00",
        "_start_at": "2013-10-14T00:00:00+00:00",
        "_timestamp": "2013-10-14T00:00:00+00:00",
        "_updated_at": "2015-01-14T12:51:45.624000+00:00",
        "_week_start_at": "2013-10-14T00:00:00+00:00",
        "_year_start_at": "2013-01-01T00:00:00+00:00",
        "rate": 0.29334396173774413
    },
]


class ComputeTestCase(unittest.TestCase):

    @patch("performanceplatform.client.AdminAPI.get_data_set_dashboard")
    def test_compute(self, mock_dashboard):
        mock_dashboard_data = [
            {
                'published': True,
                'slug': 'published'
            },
            {
                'published': False,
                'slug': 'unpublished'
            }
        ]
        mock_dashboard.return_value = mock_dashboard_data
        transformed_data = compute(data, {}, {
            'name': 'apply_carers_allowance_completion_rate',
            'data_type': 'completion-rate'
        })

        assert_that(len(transformed_data), is_(1))
        assert_that(
            transformed_data[0]['_id'],
            is_(base64.b64encode(mock_dashboard_data[0]['slug'] + 'completion_rate')))
        assert_that(
            transformed_data[0]['_timestamp'],
            is_('2013-10-14T00:00:00+00:00'))
        assert_that(
            transformed_data[0]['completion_rate'], is_(0.29334396173774413))

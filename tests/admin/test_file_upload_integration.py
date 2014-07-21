# -*- coding: utf-8 -*-

from StringIO import StringIO
import os
import datetime
from hamcrest import (assert_that, has_entry, is_, has_entries, has_items,
                      equal_to)
from pymongo import MongoClient
from tests.support.performanceplatform_client import fake_data_set_exists, stub_user_retrieve_by_email
from tests.support.test_helpers import has_status
from tests.admin.support.clamscan import stub_clamscan
from tests.admin.support.oauth_test_case import OauthTestCase
from mock import patch
from mock import Mock
from requests.exceptions import RequestException
from backdrop.core.errors import ValidationError


class TestFileUploadIntegration(OauthTestCase):
    def _drop_collection(self, collection):
        db = MongoClient('localhost', 27017).backdrop_test
        db[collection].drop()

    def _sign_in(self, email):
        self.given_user_is_signed_in_as(
            name="test",
            email=email)

    @fake_data_set_exists("test", upload_format="csv")
    @stub_user_retrieve_by_email("test@example.com", data_sets=["test"])
    @stub_clamscan(is_virus=False)
    @patch("performanceplatform.client.DataSet.post")
    def test_accepts_content_type_for_csv(self, mock_post):
        self._sign_in("test@example.com")
        response = self.do_simple_file_post()

        assert_that(response, has_status(200))

    @fake_data_set_exists("test", upload_format="csv")
    @stub_user_retrieve_by_email("test@example.com", data_sets=["test"])
    @stub_clamscan(is_virus=True)
    @patch("performanceplatform.client.DataSet.from_group_and_type")
    def test_rejects_content_type_for_exe(self, mock_from_group_and_type):
        self._sign_in("test@example.com")

        response = self.client.post(
            'test/upload',
            data = {
                'file': (StringIO('virus virus virus'), 'kittens.exe')
            }
        )

        assert_that(response, has_status(400))

    @fake_data_set_exists(
        "test_upload_integration",
        upload_format="csv",
        bearer_token="some_nonsense",
        data_group="test",
        data_type="upload_integration")
    @stub_user_retrieve_by_email("test@example.com", data_sets=["test_upload_integration"])
    @stub_clamscan(is_virus=False)
    @patch("performanceplatform.client.DataSet")
    def test_data_hits_the_backdrop_client_when_uploading_csv(
            self, mock_client_class):
        self._sign_in("test@example.com")
        self._drop_collection('test_upload_integration')
        mock_post = get_mock_post(mock_client_class)
        response = self.client.post(
            'test_upload_integration/upload',
            data = {
                'file': (StringIO('_id,value\nhello,some_value'), 'data.csv')
            }
        )

        mock_client_class.from_group_and_type.assert_called_once_with(
            'http://localhost:3039/data',
            'test',
            'upload_integration',
            token='some_nonsense'
        )
        mock_post.assert_called_once_with([{u'_id': u'hello', u'value': u'some_value'}])
        assert_that(response, has_status(200))

    @fake_data_set_exists(
        "test_upload_integration",
        upload_format="csv",
        bearer_token="some_nonsense",
        data_group="test",
        data_type="upload_integration")
    @stub_user_retrieve_by_email("test@example.com", data_sets=["test_upload_integration"])
    @stub_clamscan(is_virus=False)
    @patch("performanceplatform.client.DataSet")
    def test_uploaded_csv_file_contains_utf8(
            self, mock_client_class):
        self._sign_in("test@example.com")
        mock_post = get_mock_post(mock_client_class)
        response = self.client.post(
            'test_upload_integration/upload',
            data = {
                'file': (StringIO(u'english,italian\ncity,città\ncoffee,caffè'.encode('utf-8')), 'data.csv')
            }
        )

        mock_client_class.from_group_and_type.assert_called_once_with(
            'http://localhost:3039/data',
            'test',
            'upload_integration',
            token='some_nonsense'
        )
        mock_post.assert_called_once_with([
            {u'english': u'city', u'italian': u'città'},
            {u'english': u'coffee', u'italian': u'caffè'}])
        assert_that(response, has_status(200))

    @fake_data_set_exists(
        "integration_test_excel_data_set",
        upload_format="excel",
        bearer_token="some_nonsense",
        data_group="test",
        data_type="upload_integration")
    @stub_user_retrieve_by_email("test@example.com", data_sets=["integration_test_excel_data_set"])
    @stub_clamscan(is_virus=False)
    @patch("performanceplatform.client.DataSet")
    def test_data_hits_the_backdrop_client_when_uploading_xlsx(self, mock_client_class):
        self._drop_collection('integration_test_excel_data_set')
        self._sign_in("test@example.com")

        mock_post = get_mock_post(mock_client_class)

        fixture_path = os.path.join('features', 'fixtures', 'data.xlsx')
        response = self.client.post(
            'integration_test_excel_data_set/upload',
            data = {
                'file': open(fixture_path)
            }
        )

        mock_client_class.from_group_and_type.assert_called_once_with(
            'http://localhost:3039/data',
            'test',
            'upload_integration',
            token='some_nonsense'
        )
        mock_post.assert_called_once_with([{u'nationality': u'Polish', u'age': 27.0, u'name': u'Pawel'}, {u'nationality': u'Italian', u'age': 35.0, u'name': u'Max'}])
        assert_that(response, has_status(200))

    @fake_data_set_exists("test", upload_format="csv")
    @stub_user_retrieve_by_email("test@example.com", data_sets=["test"])
    @stub_clamscan(is_virus=False)
    @patch("performanceplatform.client.DataSet.post")
    def test_error_cases_when_post_to_backdrop_fails(self, mock_post):
        self._sign_in("test@example.com")
        mock_post.side_effect = RequestException()
        response = self.do_simple_file_post()
        assert_that(response, has_status(500))

    @fake_data_set_exists("test", upload_format="csv")
    @stub_user_retrieve_by_email("test@example.com", data_sets=["test"])
    @stub_clamscan(is_virus=False)
    @patch("backdrop.core.upload.create_parser")
    def test_error_cases_when_upload_validation_fails(self, mock_parser):
        self._sign_in("test@example.com")
        mock_parser.side_effect = ValidationError()
        response = self.do_simple_file_post()
        assert_that(response, has_status(500))

    @fake_data_set_exists("evl_ceg_data", data_group="group", data_type="type", upload_format="excel", upload_filters=["backdrop.core.upload.filters.first_sheet_filter", "backdrop.contrib.evl_upload_filters.ceg_volumes"], bearer_token="some_token")
    @stub_user_retrieve_by_email("test@example.com", data_sets=["evl_ceg_data"])
    @stub_clamscan(is_virus=False)
    @patch("performanceplatform.client.DataSet")
    def test_upload_evl_ceg_data(self, mock_client_class):
        self._sign_in("test@example.com")

        mock_post = get_mock_post(mock_client_class)

        fixture_path = os.path.join('features', 'fixtures', 'contrib',
                                    'CEG Transaction Tracker.xlsx')
        response = self.client.post(
            'evl_ceg_data/upload',
            data={
                'file': open(fixture_path)
            }
        )

        mock_client_class.from_group_and_type.assert_called_once_with(
            'http://localhost:3039/data',
            'group',
            'type',
            token='some_token'
        )
        stored_filtered_data = {
            "calls_answered_by_advisor": 56383,
            "sorn_web": 108024,
            "_timestamp": '2007-07-01T00:00:00+00:00'
        }
        # This is definitely not incredibly obtuse
        # it is basically saying that one of the bits of data that we posted
        # has this entries in it which have something to do with the operation of a filter
        # this could not work if filters were not working... apparently.
        pos_args = mock_post.call_args[0]
        post_arg = pos_args[0]
        assert_that(post_arg[0], has_entries(stored_filtered_data))
        assert_that(len(post_arg), equal_to(71))
        assert_that(response, has_status(200))

    @fake_data_set_exists("evl_services_volumetrics", data_group="group", data_type="type", upload_format="excel", upload_filters=["backdrop.core.upload.filters.first_sheet_filter", "backdrop.contrib.evl_upload_filters.service_volumetrics"], bearer_token="some_token")
    @stub_user_retrieve_by_email("test@example.com", data_sets=["evl_services_volumetrics"])
    @stub_clamscan(is_virus=False)
    @patch("performanceplatform.client.DataSet")
    def test_upload_evl_service_volumetrics(self, mock_client_class):
        self._sign_in("test@example.com")

        mock_post = get_mock_post(mock_client_class)

        fixture_path = os.path.join('features', 'fixtures', 'contrib',
                                    'EVL Services Volumetrics Sample.xls')
        response = self.client.post(
            'evl_services_volumetrics/upload',
            data={
                'file': open(fixture_path)
            }
        )

        mock_client_class.from_group_and_type.assert_called_once_with(
            'http://localhost:3039/data',
            'group',
            'type',
            token='some_token'
        )

        stored_filtered_data = {
            "_timestamp": "2013-08-01T00:00:00+00:00",
            "_id": "2013-08-01",
            "timeSpan": "day",
            "successful_tax_disc": 100.0,
            "successful_sorn": 200.0
        }

        pos_args = mock_post.call_args[0]
        post_arg = pos_args[0]
        assert_that(post_arg[0], has_entries(stored_filtered_data))
        assert_that(len(post_arg), equal_to(1))
        assert_that(response, has_status(200))

    @fake_data_set_exists("evl_services_failures", data_group="group", data_type="type", upload_format="excel", upload_filters=["backdrop.contrib.evl_upload_filters.service_failures"], bearer_token="some_token")
    @stub_user_retrieve_by_email("test@example.com", data_sets=["evl_services_failures"])
    @stub_clamscan(is_virus=False)
    @patch("performanceplatform.client.DataSet")
    def test_upload_evl_service_failures(self, mock_client_class):
        self._sign_in("test@example.com")

        mock_post = get_mock_post(mock_client_class)

        fixture_path = os.path.join('features', 'fixtures', 'contrib',
                                    'EVL Services Volumetrics Sample.xls')
        response = self.client.post(
            'evl_services_failures/upload',
            data={
                'file': open(fixture_path)
            }
        )

        mock_client_class.from_group_and_type.assert_called_once_with(
            'http://localhost:3039/data',
            'group',
            'type',
            token='some_token'
        )

        stored_filtered_data = [
            {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01.tax-disc.0", "type": "tax-disc", "reason": 0, "count": 1, "description": "Abandoned"},
            {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01.tax-disc.66", "type": "tax-disc", "reason": 66, "count": 67, "description": "LPB Response Code was PSP Session Timeout"},
            {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01.sorn.5", "type": "sorn", "reason": 5, "count": 8, "description": "User Cancelled Transaction"},
        ]

        pos_args = mock_post.call_args[0]
        post_arg = pos_args[0]
        assert_that(post_arg, has_items(*stored_filtered_data))
        assert_that(len(post_arg), equal_to(136))
        assert_that(response, has_status(200))

    @fake_data_set_exists("evl_channel_volumetrics", data_group="group", data_type="type", upload_format="excel", upload_filters=["backdrop.core.upload.filters.first_sheet_filter", "backdrop.contrib.evl_upload_filters.channel_volumetrics"], bearer_token="some_token")
    @stub_user_retrieve_by_email("test@example.com", data_sets=["evl_channel_volumetrics"])
    @stub_clamscan(is_virus=False)
    @patch("performanceplatform.client.DataSet")
    def test_upload_evl_channel_volumetrics(self, mock_client_class):
        self._sign_in("test@example.com")

        mock_post = get_mock_post(mock_client_class)

        fixture_path = os.path.join('features', 'fixtures', 'contrib',
                                    'EVL Channel Volumetrics Sample.xls')
        response = self.client.post(
            'evl_channel_volumetrics/upload',
            data={
                'file': open(fixture_path)
            }
        )

        mock_client_class.from_group_and_type.assert_called_once_with(
            'http://localhost:3039/data',
            'group',
            'type',
            token='some_token'
        )

        stored_filtered_data = [
            {"_timestamp": "2013-07-29T00:00:00+00:00", "_id": "2013-07-29", "successful_agent": 100.0, "successful_ivr": 101.0, "successful_web": 102.0, "total_agent": 200.0, "total_ivr": 201.0, "total_web": 202.0},
            {"_timestamp": "2013-07-30T00:00:00+00:00", "_id": "2013-07-30", "successful_agent": 101.0, "successful_ivr": 102.0, "successful_web": 103.0, "total_agent": 201.0, "total_ivr": 202.0, "total_web": 203.0},
        ]

        pos_args = mock_post.call_args[0]
        post_arg = pos_args[0]
        assert_that(post_arg, has_items(*stored_filtered_data))
        assert_that(len(post_arg), equal_to(2))
        assert_that(response, has_status(200))

    @fake_data_set_exists("evl_customer_satisfaction", data_group="group", data_type="type", upload_format="excel", upload_filters=["backdrop.core.upload.filters.first_sheet_filter", "backdrop.contrib.evl_upload_filters.customer_satisfaction"], bearer_token="some_token")
    @stub_user_retrieve_by_email("test@example.com", data_sets=["evl_customer_satisfaction"])
    @stub_clamscan(is_virus=False)
    @patch("performanceplatform.client.DataSet")
    def test_upload_evl_customer_satisfaction(self, mock_client_class):
        self._sign_in("test@example.com")

        mock_post = get_mock_post(mock_client_class)

        fixture_path = os.path.join('features', 'fixtures', 'contrib',
                                    'EVL Customer Satisfaction.xlsx')
        response = self.client.post(
            'evl_customer_satisfaction/upload',
            data={
                'file': open(fixture_path)
            }
        )

        mock_client_class.from_group_and_type.assert_called_once_with(
            'http://localhost:3039/data',
            'group',
            'type',
            token='some_token'
        )

        stored_filtered_data = [
            {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01", "satisfaction_tax_disc": 1.2487024060928635, "satisfaction_sorn": 1.4370298628996634},
            {"_timestamp": "2007-07-01T00:00:00+00:00", "_id": "2007-07-01", "satisfaction_tax_disc": 1.1662755514934828, "satisfaction_sorn": 1.3581011781786714},
        ]

        pos_args = mock_post.call_args[0]
        post_arg = pos_args[0]
        assert_that(post_arg, has_items(*stored_filtered_data))
        assert_that(len(post_arg), equal_to(113))
        assert_that(response, has_status(200))

    @fake_data_set_exists("evl_volumetrics", data_group="group", data_type="type", upload_format="excel", upload_filters=["backdrop.contrib.evl_upload_filters.volumetrics"], bearer_token="some_token")
    @stub_user_retrieve_by_email("test@example.com", data_sets=["evl_volumetrics"])
    @stub_clamscan(is_virus=False)
    @patch("performanceplatform.client.DataSet")
    def test_upload_evl_volumetrics(self, mock_client_class):
        self._sign_in("test@example.com")

        mock_post = get_mock_post(mock_client_class)

        fixture_path = os.path.join('features', 'fixtures', 'contrib',
                                    'evl-volumetrics.xls')
        response = self.client.post(
            'evl_volumetrics/upload',
            data={
                'file': open(fixture_path)
            }
        )

        mock_client_class.from_group_and_type.assert_called_once_with(
            'http://localhost:3039/data',
            'group',
            'type',
            token='some_token'
        )

        stored_filtered_data = [
            {"_timestamp": "2012-04-01T00:00:00+00:00", "transaction": "V-V890 SORN Declaration Refunds Input", "service": "sorn", "volume": 1025.0},
            {"_timestamp": "2012-05-01T00:00:00+00:00", "transaction": "V-V890 SORN Declaration Vehicles Input", "service": "sorn", "volume": 0.0},
            {"_timestamp": "2012-06-01T00:00:00+00:00", "transaction": "V-V890 SORN Declaration Vehicles Triage", "service": "sorn", "volume": None},
        ]

        pos_args = mock_post.call_args[0]
        post_arg = pos_args[0]
        assert_that(post_arg, has_items(*[has_entries(i) for i in stored_filtered_data]))
        assert_that(len(post_arg), equal_to(336))
        assert_that(response, has_status(200))

    @fake_data_set_exists("data_set_with_timestamp_auto_id", data_group="group", data_type="type", upload_format="excel", auto_ids=["_timestamp", "key"])
    @stub_user_retrieve_by_email("test@example.com", data_sets=["data_set_with_timestamp_auto_id"])
    @stub_clamscan(is_virus=False)
    @patch("performanceplatform.client.DataSet.post")
    def test_upload_auto_generate_ids(self, mock_post):
        self._drop_collection("data_set_with_timestamp_auto_id")
        self._sign_in("test@example.com")

        fixture_path = os.path.join('features', 'fixtures',
                                    'LPA_MI_EXAMPLE.xls')
        response = self.client.post(
            'data_set_with_timestamp_auto_id/upload',
            data={
                'file': open(fixture_path)
            }
        )

        assert_that(response, has_status(200))
        assert_that(response, has_status(200))

        pos_args = mock_post.call_args[0]
        post_arg = pos_args[0]

        assert_that(len(post_arg), is_(18))

    def do_simple_file_post(self):
        return self.client.post(
            'test/upload',
            data={
                'file': (StringIO('foo, bar'), 'a_big_csv.csv')
            }
        )


def get_mock_post(mock_client_class):
    mock_post = Mock()
    client_instance = Mock()
    client_instance.post = mock_post
    mock_construction_helper = Mock()
    mock_construction_helper.return_value = client_instance
    mock_client_class.from_group_and_type = mock_construction_helper
    return mock_post

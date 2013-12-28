from StringIO import StringIO
import os
import datetime
from hamcrest import assert_that, has_entry, is_, has_entries
from pymongo import MongoClient
from tests.support.bucket import stub_bucket_retrieve_by_name, setup_bucket, stub_user_retrieve_by_email
from tests.support.clamscan import stub_clamscan
from tests.support.oauth_test_case import OauthTestCase
from tests.support.test_helpers import has_status


class TestFileUploadIntegration(OauthTestCase):
    def _drop_collection(self, collection):
        db = MongoClient('localhost', 27017).backdrop_test
        db[collection].drop()

    def _sign_in(self, email):
        self.given_user_is_signed_in_as(
            name="test",
            email=email)

    @stub_bucket_retrieve_by_name("test", upload_format="csv")
    @stub_user_retrieve_by_email("test@example.com", buckets=["test"])
    @stub_clamscan(is_virus=False)
    def test_accepts_content_type_for_csv(self):
        self._sign_in("test@example.com")
        response = self.client.post(
            'test/upload',
            data={
                'file': (StringIO('foo, bar'), 'a_big_csv.csv')
            }
        )

        assert_that(response, has_status(200))

    @stub_bucket_retrieve_by_name("test", upload_format="csv")
    @stub_user_retrieve_by_email("test@example.com", buckets=["test"])
    @stub_clamscan(is_virus=True)
    def test_rejects_content_type_for_exe(self):
        self._sign_in("test@example.com")

        response = self.client.post(
            'test/upload',
            data = {
                'file': (StringIO('virus virus virus'), 'kittens.exe')
            }
        )

        assert_that(response, has_status(400))

    @stub_bucket_retrieve_by_name("test_upload_integration", upload_format="csv")
    @stub_user_retrieve_by_email("test@example.com", buckets=["test_upload_integration"])
    @stub_clamscan(is_virus=False)
    def test_data_hits_the_database_when_uploading_csv(self):
        self._sign_in("test@example.com")
        self._drop_collection('test_upload_integration')

        response = self.client.post(
            'test_upload_integration/upload',
            data = {
                'file': (StringIO('_id,value\nhello,some_value'), 'data.csv')
            }
        )

        assert_that(response, has_status(200))
        db = MongoClient('localhost', 27017).backdrop_test
        record = list(db.test_upload_integration.find({'_id': 'hello'}))[0]

        assert_that(record, has_entry('_id', 'hello'))
        assert_that(record, has_entry('value', 'some_value'))

    @stub_bucket_retrieve_by_name("integration_test_excel_bucket", upload_format="excel")
    @stub_user_retrieve_by_email("test@example.com", buckets=["integration_test_excel_bucket"])
    @stub_clamscan(is_virus=False)
    def test_data_hits_the_database_when_uploading_xlsx(self):
        self._drop_collection('integration_test_excel_bucket')
        self._sign_in("test@example.com")
        fixture_path = os.path.join('features', 'fixtures', 'data.xlsx')
        response = self.client.post(
            'integration_test_excel_bucket/upload',
            data = {
                'file': open(fixture_path)
            }
        )

        assert_that(response, has_status(200))
        db = MongoClient('localhost', 27017).backdrop_test
        record = list(db.integration_test_excel_bucket.find(
            {'name': 'Pawel'}))[0]

        assert_that(record, has_entry('age', 27))
        assert_that(record, has_entry('nationality', 'Polish'))

    @setup_bucket("evl_ceg_data", data_group="group", data_type="type", upload_format="excel", upload_filters=["backdrop.core.upload.filters.first_sheet_filter", "backdrop.contrib.evl_upload_filters.ceg_volumes"])
    @stub_user_retrieve_by_email("test@example.com", buckets=["evl_ceg_data"])
    @stub_clamscan(is_virus=False)
    def test_upload_applies_filters(self):
        self._drop_collection("evl_ceg_data")
        self._sign_in("test@example.com")

        fixture_path = os.path.join('features', 'fixtures', 'contrib',
                                    'CEG Transaction Tracker.xlsx')
        response = self.client.post(
            'evl_ceg_data/upload',
            data={
                'file': open(fixture_path)
            }
        )

        assert_that(response, has_status(200))
        db = MongoClient('localhost', 27017).backdrop_test
        results = list(db.evl_ceg_data.find())

        assert_that(len(results), is_(71))
        assert_that(results[0], has_entries({
            "calls_answered_by_advisor": 56383,
            "sorn_web": 108024,
            "_timestamp": datetime.datetime(2007, 7, 1, 0, 0),
        }))

    @setup_bucket("bucket_with_timestamp_auto_id", data_group="group", data_type="type", upload_format="excel", auto_ids=["_timestamp", "key"])
    @stub_user_retrieve_by_email("test@example.com", buckets=["bucket_with_timestamp_auto_id"])
    @stub_clamscan(is_virus=False)
    def test_upload_auto_generate_ids(self):
        self._drop_collection("bucket_with_timestamp_auto_id")
        self._sign_in("test@example.com")

        fixture_path = os.path.join('features', 'fixtures',
                                    'LPA_MI_EXAMPLE.xls')
        response = self.client.post(
            'bucket_with_timestamp_auto_id/upload',
            data={
                'file': open(fixture_path)
            }
        )

        assert_that(response, has_status(200))
        db = MongoClient('localhost', 27017).backdrop_test
        results = list(db.bucket_with_timestamp_auto_id.find())

        assert_that(len(results), is_(18))
        assert_that(results[0], has_entries({
            "_id": "MjAxMy0wNy0wMVQwMDowMDowMCswMDowMC5wcm9wZXJ0eV9hbmRfZmluYW5jaWFsX2Zvcm1zX3Bvc3RlZA==",
        }))

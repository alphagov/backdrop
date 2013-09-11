from StringIO import StringIO
import os
from hamcrest import assert_that, has_entry
from pymongo import MongoClient
from tests.support.oauth_test_case import OauthTestCase
from tests.support.test_helpers import has_status


class TestFileUploadIntegration(OauthTestCase):
    def _drop_collection(self, collection):
        db = MongoClient('localhost', 27017).backdrop_test
        db[collection].drop()

    def _sign_in(self):
        self.given_user_is_signed_in_with_permissions(
            name="test",
            email="test@example.com",
            buckets=["test", "test_upload_integration", "integration_test_excel_bucket"]
        )

    def test_accepts_content_type_for_csv(self):
        self._sign_in()
        response = self.client.post(
            'test/upload',
            data={
                'file': (StringIO('foo, bar'), 'a_big_csv.csv')
            }
        )

        assert_that(response, has_status(200))

    def test_rejects_content_type_for_exe(self):
        self._sign_in()

        response = self.client.post(
            'test/upload',
            data = {
                'file': (StringIO('virus virus virus'), 'kittens.exe')
            }
        )

        assert_that(response, has_status(400))

    def test_data_hits_the_database_when_uploading_csv(self):
        self._sign_in()
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

    def test_data_hits_the_database_when_uploading_xlsx(self):
        self._drop_collection('integration_test_excel_bucket')
        self._sign_in()
        fixture_path = os.path.join('features', 'fixtures', 'data.xlsx')
        response = self.client.post(
            'integration_test_excel_bucket/upload',
            data = {
                 'file': open(fixture_path)
            }

        )

        assert_that(response,has_status(200))
        db = MongoClient('localhost', 27017).backdrop_test
        record = list(db.integration_test_excel_bucket.find(
            {'name': 'Pawel'}))[0]

        assert_that(record,has_entry('age', 27))
        assert_that(record,has_entry('nationality', 'Polish'))

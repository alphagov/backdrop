import unittest
import mock

from contextlib import contextmanager

from os.path import dirname, join as pjoin

from hamcrest import assert_that, is_, has_entries
from backdrop.core.bucket import BucketConfig
from backdrop.core.database import Database
from backdrop.core.repository import BucketConfigRepository, UserConfigRepository
from backdrop.core.user import UserConfig

HOST = ['localhost']
PORT = 27017
DB_NAME = 'performance_platform_test'
BUCKET = 'buckets'
STAGECRAFT_URL = 'fake_url_should_not_be_called'
STAGECRAFT_DATA_SET_QUERY_TOKEN = 'fake_token_should_not_be_used'


@contextmanager
def fixture(name):
    filename = pjoin(dirname(__file__), '..', '..', 'fixtures', name)
    with open(filename, 'r') as f:
        yield f.read()


class TestBucketRepositoryIntegration(unittest.TestCase):

    def setUp(self):
        self.db = Database(HOST, PORT, DB_NAME)
        self.db._mongo.drop_database(DB_NAME)
        self.mongo_collection = self.db.get_collection(BUCKET)
        self.repository = BucketConfigRepository(
            STAGECRAFT_URL, STAGECRAFT_DATA_SET_QUERY_TOKEN)

    def test_retrieves_config_by_name(self):
        with fixture('stagecraft_get_single_data_set.json') as content:
            with mock.patch('backdrop.core.repository._get_url') as mocked:
                mocked.return_value = content
                config = self.repository.retrieve(name="govuk_visitors")
                mocked.assert_called_once_with(
                    'fake_url_should_not_be_called/data-sets/govuk_visitors')

        assert_that(config.name, is_('govuk_visitors'))

    def test_retrieves_config_for_service_and_data_type(self):
        with fixture('stagecraft_query_data_group_type.json') as content:
            with mock.patch('backdrop.core.repository._get_url') as mocked:
                mocked.return_value = content
                config = self.repository.get_bucket_for_query(
                    data_group="govuk", data_type="realtime")

        assert_that(config.name, is_("govuk_realtime"))


class TestUserRepositoryIntegration(object):
    def setUp(self):
        self.db = Database(HOST, PORT, DB_NAME)
        self.db._mongo.drop_database(DB_NAME)
        self.mongo_collection = self.db.get_collection("users")._collection
        self.mongo_collection.drop()
        self.repository = UserConfigRepository(self.db)

    def test_saving_a_config_with_no_buckets(self):
        config = UserConfig(email="test@example.com")

        self.repository.save(config)

        results = list(self.mongo_collection.find())

        assert_that(len(results), is_(1))
        assert_that(results[0], has_entries({
            "email": "test@example.com",
            "buckets": [],
        }))

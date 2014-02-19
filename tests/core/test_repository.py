import json
import mock
import unittest

from backdrop.core.bucket import BucketConfig
from backdrop.core.repository import (BucketConfigRepository,
                                      UserConfigRepository)
from hamcrest import assert_that, equal_to, is_, has_entries, match_equality
from mock import Mock
from nose.tools import assert_raises
from backdrop.core.user import UserConfig


class TestBucketRepository(unittest.TestCase):
    def setUp(self):
        # This is a bit of a smell. Mongo collection responsibilites should be
        # split with repo, once we have more than one repository.
        self.db = Mock()
        self.mongo_collection = Mock()
        self.db.get_collection.return_value = self.mongo_collection
        self.bucket_repo = BucketConfigRepository(
            'fake_stagecraft_url', 'fake_stagecraft_token')

    def test_bucket_config_is_created_from_retrieved_data(self):
        fake_stagecraft_response = json.dumps({
            "name": "bucket_name",
            "data_group": "data_group",
            "data_type": "type",
            "raw_queries_allowed": False,
            "bearer_token": "my-bearer-token",
            "upload_format": "excel"
        })
        with mock.patch('backdrop.core.repository._get_url') as mocked:
            mocked.return_value = fake_stagecraft_response

            bucket = self.bucket_repo.retrieve(name="bucket_name")

        expected_bucket = BucketConfig("bucket_name",
                                       data_group="data_group",
                                       data_type="type",
                                       raw_queries_allowed=False,
                                       bearer_token="my-bearer-token",
                                       upload_format="excel")

        assert_that(bucket, equal_to(expected_bucket))

    def test_retrieving_non_existent_bucket_returns_none(self):
        self.mongo_collection.find_one.return_value = None

        with mock.patch('backdrop.core.repository._get_url') as mocked:
            mocked.return_value = None
            bucket = self.bucket_repo.retrieve(name="non_existent")

        assert_that(bucket, is_(None))


class TestUserConfigRepository(object):
    def setUp(self):
        self.db = Mock()
        self.mongo_collection = Mock()
        self.db.get_collection.return_value = self.mongo_collection
        self.repository = UserConfigRepository(self.db)

    def test_saving_a_user_config(self):
        user = UserConfig("test@example.com",
                          buckets=["bucket_one", "bucket_two"])

        self.repository.save(user)
        self.mongo_collection.save.assert_called_with(
            match_equality(has_entries({
                "_id": "test@example.com",
                "buckets": ["bucket_one", "bucket_two"]
            }))
        )

    def test_saving_fails_with_non_user_config_object(self):
        not_user = {"foo": "bar"}

        assert_raises(ValueError, self.repository.save, not_user)

    def test_retrieving_a_user_config(self):
        self.mongo_collection.find_one.return_value = {
            "_id": "test@example.com",
            "email": "test@example.com",
            "buckets": ["foo", "bar"],
        }

        user_config = self.repository.retrieve(email="test@example.com")
        expected_user_config = UserConfig("test@example.com", ["foo", "bar"])

        assert_that(user_config, equal_to(expected_user_config))

    def test_retrieving_non_existent_user_config_returns_none(self):
        self.mongo_collection.find_one.return_value = None
        user_config = self.repository.retrieve(email="test@example.com")

        assert_that(user_config, is_(None))

from collections import namedtuple
from backdrop.core.bucket import BucketConfig
from backdrop.core.repository import BucketRepository
from hamcrest import assert_that, equal_to, is_, has_entries, match_equality
from mock import Mock
from nose.tools import *


class TestBucketRepository(object):
    def test_saving_a_bucket(self):
        mongo_collection = Mock()
        bucket_repo = BucketRepository(mongo_collection)

        bucket = BucketConfig("bucket_name")

        bucket_repo.save(bucket)
        mongo_collection.save.assert_called_with(match_equality(has_entries({
            "_id": "bucket_name",
            "name": "bucket_name",
            "raw_queries_allowed": False,
            "bearer_token": None,
            "upload_format": "csv",
        })))

    def test_saving_a_bucket_with_some_attributes(self):
        mongo_collection = Mock()
        bucket_repo = BucketRepository(mongo_collection)

        bucket = BucketConfig("bucket_name",
                              raw_queries_allowed=True,
                              upload_format="excel")

        bucket_repo.save(bucket)
        mongo_collection.save.assert_called_with(match_equality(has_entries({
            "_id": "bucket_name",
            "name": "bucket_name",
            "raw_queries_allowed": True,
            "bearer_token": None,
            "upload_format": "excel",
        })))

    def test_saving_fails_with_non_bucket_object(self):
        mongo_collection = Mock()
        bucket_repo = BucketRepository(mongo_collection)

        not_bucket = {"foo": "bar"}

        assert_raises(ValueError, bucket_repo.save, not_bucket)

    def test_saving_fails_with_non_bucket_namedtuple(self):
        mongo_collection = Mock()
        bucket_repo = BucketRepository(mongo_collection)

        NotBucket = namedtuple("NotBucket", "name raw_queries_allowed")
        not_bucket = NotBucket("name", True)
        assert_raises(ValueError, bucket_repo.save, not_bucket)

    def test_bucket_config_is_created_from_retrieved_data(self):
        mongo_collection = Mock()
        bucket_repo = BucketRepository(mongo_collection)

        mongo_collection.find_one.return_value = {
            "_id": "bucket_name",
            "name": "bucket_name",
            "raw_queries_allowed": False,
            "bearer_token": "my-bearer-token",
            "upload_format": "excel"
        }
        bucket = bucket_repo.retrieve(name="bucket_name")
        expected_bucket = BucketConfig("bucket_name",
                                       raw_queries_allowed=False,
                                       bearer_token="my-bearer-token",
                                       upload_format="excel")

        assert_that(bucket, equal_to(expected_bucket))

    def test_retrieving_non_existent_bucket_returns_none(self):
        mongo_collection = Mock()
        bucket_repo = BucketRepository(mongo_collection)

        mongo_collection.find_one.return_value = None
        bucket = bucket_repo.retrieve(name="bucket_name")

        assert_that(bucket, is_(None))

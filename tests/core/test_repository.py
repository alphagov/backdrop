import unittest
from collections import namedtuple
from backdrop.core.bucket import BucketConfig
from backdrop.core.repository import BucketConfigRepository
from hamcrest import assert_that, equal_to, is_, has_entries, match_equality
from mock import Mock
from nose.tools import *


class TestBucketRepository(unittest.TestCase):
    def setUp(self):
        # This is a bit of a smell. Mongo collection responsibilites should be
        # split with repo, once we have more than one repository.
        self.db = Mock()
        self.mongo_collection = Mock()
        self.db.get_collection.return_value = self.mongo_collection
        self.bucket_repo = BucketConfigRepository(self.db)

    def test_saving_a_bucket(self):
        bucket = BucketConfig("bucket_name", data_group="data_group", data_type="type")

        self.bucket_repo.save(bucket)
        self.mongo_collection.save.assert_called_with(match_equality(has_entries({
            "_id": "bucket_name",
            "name": "bucket_name",
            "data_group": "data_group",
            "data_type": "type",
            "raw_queries_allowed": False,
            "bearer_token": None,
            "upload_format": "csv",
        })))

    def test_saving_a_bucket_with_some_attributes(self):
        bucket = BucketConfig("bucket_name",
                              data_group="data_group", data_type="type",
                              raw_queries_allowed=True,
                              upload_format="excel")

        self.bucket_repo.save(bucket)
        self.mongo_collection.save.assert_called_with(match_equality(has_entries({
            "_id": "bucket_name",
            "name": "bucket_name",
            "data_group": "data_group",
            "data_type": "type",
            "raw_queries_allowed": True,
            "bearer_token": None,
            "upload_format": "excel",
        })))

    def test_saving_fails_with_non_bucket_object(self):
        not_bucket = {"foo": "bar"}

        assert_raises(ValueError, self.bucket_repo.save, not_bucket)

    def test_saving_fails_with_non_bucket_namedtuple(self):
        NotBucket = namedtuple("NotBucket", "name raw_queries_allowed")
        not_bucket = NotBucket("name", True)
        assert_raises(ValueError, self.bucket_repo.save, not_bucket)

    def test_bucket_config_is_created_from_retrieved_data(self):
        self.mongo_collection.find_one.return_value = {
            "_id": "bucket_name",
            "name": "bucket_name",
            "data_group": "data_group",
            "data_type": "type",
            "raw_queries_allowed": False,
            "bearer_token": "my-bearer-token",
            "upload_format": "excel"
        }
        bucket = self.bucket_repo.retrieve(name="bucket_name")
        expected_bucket = BucketConfig("bucket_name",
                                       data_group="data_group", data_type="type",
                                       raw_queries_allowed=False,
                                       bearer_token="my-bearer-token",
                                       upload_format="excel")

        assert_that(bucket, equal_to(expected_bucket))

    def test_saving_a_realtime_bucket_creates_a_capped_collection(self):
        capped_bucket = BucketConfig("capped_bucket",
                                     data_group="data_group", data_type="type",
                                     realtime=True, capped_size=7665)

        self.bucket_repo.save(capped_bucket)

        self.db.create_capped_collection.assert_called_with("capped_bucket", 7665)

    def test_saving_a_realtime_bucket_does_not_create_a_collection_if_creation_flag_is_off(self):
        capped_bucket = BucketConfig("capped_bucket",
                                     data_group="data_group", data_type="type",
                                     realtime=True, capped_size=7665)

        self.bucket_repo.save(capped_bucket, create_bucket=False)

        assert not self.db.create_capped_collection.called

    def test_retrieving_non_existent_bucket_returns_none(self):
        self.mongo_collection.find_one.return_value = None
        bucket = self.bucket_repo.retrieve(name="bucket_name")

        assert_that(bucket, is_(None))

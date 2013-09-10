from backdrop.core.repository import BucketRepository
from backdrop.core.bucket_new import Bucket
from hamcrest import assert_that, equal_to, is_
from mock import Mock


class TestBucketRepository(object):
    def test_saving_a_bucket(self):
        mongo_collection = Mock()
        bucket_repo = BucketRepository(mongo_collection)

        bucket = Bucket("bucket_name")

        bucket_repo.save(bucket)
        mongo_collection.save.assert_called_with({
            "_id": "bucket_name",
            "name": "bucket_name",
            "raw_queries_allowed": False,
        })

    def test_saving_a_bucket_with_raw_queries_allowed(self):
        mongo_collection = Mock()
        bucket_repo = BucketRepository(mongo_collection)

        bucket = Bucket("bucket_name", raw_queries_allowed=True)

        bucket_repo.save(bucket)
        mongo_collection.save.assert_called_with({
            "_id": "bucket_name",
            "name": "bucket_name",
            "raw_queries_allowed": True
        })

    def test_retrieving_a_bucket(self):
        mongo_collection = Mock()
        bucket_repo = BucketRepository(mongo_collection)

        mongo_collection.find_one.return_value = {
            "_id": "bucket_name",
            "name": "bucket_name",
            "raw_queries_allowed": False,
        }
        bucket = bucket_repo.retrieve(name="bucket_name")

        assert_that(bucket, equal_to(Bucket("bucket_name")))

    def test_retrieving_non_existent_bucket_returns_none(self):
        mongo_collection = Mock()
        bucket_repo = BucketRepository(mongo_collection)

        mongo_collection.find_one.return_value = None
        bucket = bucket_repo.retrieve(name="bucket_name")

        assert_that(bucket, is_(None))

    def test_retrieving_a_bucket_with_raw_queries_allowed(self):
        mongo_collection = Mock()
        bucket_repo = BucketRepository(mongo_collection)

        mongo_collection.find_one.return_value = {
            "_id": "bucket_name",
            "name": "bucket_name",
            "raw_queries_allowed": True,
        }
        bucket = bucket_repo.retrieve(name="bucket_name")

        assert_that(bucket, equal_to(Bucket("bucket_name", True)))

import unittest
from hamcrest import assert_that, is_, has_entries
from backdrop.core.bucket import BucketConfig
from backdrop.core.database import MongoDriver
from pymongo import MongoClient
from backdrop.core.repository import BucketRepository

HOST = 'localhost'
PORT = 27017
DB_NAME = 'performance_platform_test'
BUCKET = 'buckets_config_test'


class TestBucketRepositoryIntegration(unittest.TestCase):

    def setUp(self):
        mongo_driver = MongoDriver(MongoClient(HOST, PORT)[DB_NAME][BUCKET])
        mongo_driver._collection.drop()
        self.mongo_collection = MongoClient(HOST, PORT)[DB_NAME][BUCKET]
        self.repository = BucketRepository(mongo_driver)

    def test_saving_a_config_with_default_values(self):
        config = BucketConfig("some_bucket")

        self.repository.save(config)

        results = list(self.mongo_collection.find())

        assert_that(len(results), is_(1))
        assert_that(results[0], has_entries({
            "name": "some_bucket",
            "raw_queries_allowed": False,
            "bearer_token": None,
            "upload_format": "csv"
        }))

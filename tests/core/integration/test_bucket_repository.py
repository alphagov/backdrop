import unittest
from hamcrest import assert_that, is_, has_entries
from nose.tools import nottest
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
        config = BucketConfig("some_bucket", data_group="group", data_type="type")

        self.repository.save(config)

        results = list(self.mongo_collection.find())

        assert_that(len(results), is_(1))
        assert_that(results[0], has_entries({
            "name": "some_bucket",
            "raw_queries_allowed": False,
            "bearer_token": None,
            "upload_format": "csv"
        }))

    def test_retrieves_config_by_name(self):
        self.repository.save(BucketConfig("not_my_bucket", data_group="group", data_type="type"))
        self.repository.save(BucketConfig("my_bucket", data_group="group", data_type="type"))
        self.repository.save(BucketConfig("someones_bucket", data_group="group", data_type="type"))

        config = self.repository.retrieve(name="my_bucket")

        assert_that(config.name, is_("my_bucket"))

    def test_retrieves_config_for_service_and_data_type(self):
        self.repository.save(BucketConfig("b1", data_group="my_service", data_type="my_type"))
        self.repository.save(BucketConfig("b2", data_group="my_service", data_type="not_my_type"))
        self.repository.save(BucketConfig("b3", data_group="not_my_service", data_type="my_type"))

        config = self.repository.get_bucket_for_query(data_group="my_service", data_type="my_type")

        assert_that(config.name, is_("b1"))

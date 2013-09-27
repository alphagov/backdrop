import unittest
from hamcrest import assert_that, is_, has_entries
from backdrop.core.bucket import BucketConfig
from backdrop.core.database import Database
from backdrop.core.repository import BucketConfigRepository, UserConfigRepository
from backdrop.core.user import UserConfig

HOST = 'localhost'
PORT = 27017
DB_NAME = 'performance_platform_test'
BUCKET = 'buckets'


class TestBucketRepositoryIntegration(unittest.TestCase):

    def setUp(self):
        self.db = Database(HOST, PORT, DB_NAME)
        self.db._mongo.drop_database(DB_NAME)
        self.mongo_collection = self.db.get_collection(BUCKET)
        self.mongo_collection._collection.drop()
        self.repository = BucketConfigRepository(self.db)

    def test_saving_a_config_with_default_values(self):
        config = BucketConfig("some_bucket", data_group="group", data_type="type")

        self.repository.save(config)

        results = list(self.mongo_collection._collection.find())

        assert_that(len(results), is_(1))
        assert_that(results[0], has_entries({
            "name": "some_bucket",
            "raw_queries_allowed": False,
            "bearer_token": None,
            "upload_format": "csv"
        }))

    def test_saving_a_realtime_config_creates_a_capped_collection(self):
        config = BucketConfig("realtime_bucket", data_group="group", data_type="type", realtime=True)

        self.repository.save(config)

        assert_that(self.db.mongo_database["realtime_bucket"].options(), is_({"capped": True, "size": 5040}))

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

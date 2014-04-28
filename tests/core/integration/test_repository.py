from hamcrest import assert_that, is_, has_entries
from backdrop.core.database import Database
from backdrop.core.repository import UserConfigRepository
from backdrop.core.user import UserConfig

HOSTS = ['localhost']
PORT = 27017
DB_NAME = 'performance_platform_test'


class TestUserRepositoryIntegration(object):
    def setUp(self):
        self.db = Database(HOSTS, PORT, DB_NAME)
        self.db._mongo.drop_database(DB_NAME)
        self.mongo_collection = self.db.get_collection("users")._collection
        self.mongo_collection.drop()
        self.repository = UserConfigRepository(self.db)

    def test_saving_a_config_with_no_data_sets(self):
        config = UserConfig(email="test@example.com")

        self.repository.save(config)

        results = list(self.mongo_collection.find())

        assert_that(len(results), is_(1))
        assert_that(results[0], has_entries({
            "email": "test@example.com",
            "data_sets": [],
        }))

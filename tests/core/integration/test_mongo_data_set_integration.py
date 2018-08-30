import unittest

from pymongo import MongoClient

from backdrop.core.data_set import DataSet
from backdrop.core.storage.mongo import MongoStorageEngine

from .test_data_set_integration import BaseDataSetIntegrationTest

DATABASE_URL = 'mongodb://localhost:27017/backdrop_test'
DATA_SET = 'data_set_integration_test'


class TestMongoDataSetIntegration(BaseDataSetIntegrationTest, unittest.TestCase):

    def setUp(self):
        self.storage = MongoStorageEngine.create(DATABASE_URL)

        self.config = {
            'name': DATA_SET,
            'data_group': "group",
            'data_type': "type",
            'max_age_expected': 1000,
        }

        self.data_set = DataSet(self.storage, self.config)

        database = MongoClient(DATABASE_URL).get_database()
        self.mongo_collection = database[DATA_SET]

    def tearDown(self):
        self.mongo_collection.drop()

    def _save(self, obj):
        self.mongo_collection.save(obj)

import unittest

from pymongo import MongoClient
from api import DataStore

TEST_DATABASE = 'performance_platform_test'

def setup_test_database():
    # init mongo client
    mongo = MongoClient('localhost', 27017)
    # cleanup test db
    mongo.drop_database(TEST_DATABASE)
    # for collection_name in db.collection_names():
    #     db.drop_collection(collection_name)


def retrieve_data(collection_name):
    return MongoClient('localhost', 27017)[TEST_DATABASE][collection_name]\
        .find()


class MongoTestCase(unittest.TestCase):

    def setUp(self):
        setup_test_database()


    def test_object_gets_stored_in_db(self):
        my_object = {'foo': 'bar', 'zap': 'bop'}

        DataStore(TEST_DATABASE).store_data(my_object, "kittens")

        retrieved_objects = retrieve_data("kittens")

        self.assertTrue(my_object in retrieved_objects)

    def test_object_list_gets_stored_in_db(self):
        objects = [
            {"name": "Groucho"},
            {"name": "Harpo"},
            {"name": "Chico"}
        ]

        DataStore(TEST_DATABASE).store_data(objects, "marx-bros")

        retrieved_objects = retrieve_data("marx-bros")

        for o in objects:
            self.assertTrue(o in retrieved_objects)

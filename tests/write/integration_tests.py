import test_helper

import unittest

from hamcrest import *
from pymongo import MongoClient
from write.api import DataStore

TEST_DATABASE = 'performance_platform_test'


def setup_test_database():
    mongo = MongoClient('localhost', 27017)
    mongo.drop_database(TEST_DATABASE)


def retrieve_data(collection_name):
    mongo = MongoClient('localhost', 27017)
    return list(mongo[TEST_DATABASE][collection_name].find())


class MongoTestCase(unittest.TestCase):

    def setUp(self):
        setup_test_database()

    def test_object_gets_stored_in_db(self):
        my_object = {'foo': 'bar', 'zap': 'bop'}

        DataStore(TEST_DATABASE).store_data([my_object], "kittens")

        retrieved_objects = retrieve_data("kittens")

        self.assertTrue(my_object in retrieved_objects)
        assert_that( retrieved_objects, contains(my_object) )

    def test_object_list_gets_stored_in_db(self):
        objects = [
            {"name": "Groucho"},
            {"name": "Harpo"},
            {"name": "Chico"}
        ]

        DataStore(TEST_DATABASE).store_data(objects, "marx-bros")

        retrieved_objects = retrieve_data("marx-bros")

        assert_that( retrieved_objects, contains(*objects) )

    def test_stored_object_is_appended_to_collection(self):
        event = {"title": "I'm an event"}
        another_event = {"title": "I'm another event"}

        DataStore(TEST_DATABASE).store_data([event], "events")
        DataStore(TEST_DATABASE).store_data([another_event], "events")

        retrieved_objects = retrieve_data("events")
        assert_that( retrieved_objects, contains(event, another_event) )

    def test_object_with_id_is_updated(self):
        event = { "_id": "event1", "title": "I'm an event"}
        updated_event = {"_id": "event1", "title": "I'm another event"}

        DataStore(TEST_DATABASE).store_data([event], "events")
        DataStore(TEST_DATABASE).store_data([updated_event], "events")

        retrieved_objects = retrieve_data("events")
        assert_that( retrieved_objects, only_contains(updated_event) )

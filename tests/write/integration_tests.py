import test_helper

import unittest

from hamcrest import *
from pymongo import MongoClient
from backdrop.write.api import DataStore
from backdrop.write.config import test as config


def setup_test_database():
    mongo = MongoClient(config.MONGO_HOST, config.MONGO_PORT)
    mongo.drop_database(config.DATABASE_NAME)


def retrieve_data(collection_name):
    mongo = MongoClient(config.MONGO_HOST, config.MONGO_PORT)
    return list(mongo[config.DATABASE_NAME][collection_name].find())


class MongoTestCase(unittest.TestCase):

    def setUp(self):
        setup_test_database()

    def test_object_gets_stored_in_db(self):
        my_object = {'foo': 'bar', 'zap': 'bop'}

        DataStore(config.DATABASE_NAME).store_data([my_object], "kittens")

        retrieved_objects = retrieve_data("kittens")

        self.assertTrue(my_object in retrieved_objects)
        assert_that( retrieved_objects, contains(my_object) )

    def test_object_list_gets_stored_in_db(self):
        objects = [
            {"name": "Groucho"},
            {"name": "Harpo"},
            {"name": "Chico"}
        ]

        DataStore(config.DATABASE_NAME).store_data(objects, "marx-bros")

        retrieved_objects = retrieve_data("marx-bros")

        assert_that( retrieved_objects, contains(*objects) )

    def test_stored_object_is_appended_to_collection(self):
        event = {"title": "I'm an event"}
        another_event = {"title": "I'm another event"}

        DataStore(config.DATABASE_NAME).store_data([event], "events")
        DataStore(config.DATABASE_NAME).store_data([another_event], "events")

        retrieved_objects = retrieve_data("events")
        assert_that( retrieved_objects, contains(event, another_event) )

    def test_object_with_id_is_updated(self):
        event = { "_id": "event1", "title": "I'm an event"}
        updated_event = {"_id": "event1", "title": "I'm another event"}

        DataStore(config.DATABASE_NAME).store_data([event], "events")
        DataStore(config.DATABASE_NAME).store_data([updated_event], "events")

        retrieved_objects = retrieve_data("events")
        assert_that( retrieved_objects, only_contains(updated_event) )

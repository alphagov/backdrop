import unittest
from hamcrest import *
from pymongo import MongoClient
from backdrop.core.repository import Repository

HOST = 'localhost'
PORT = 27017
DB_NAME = 'performance_platform_test'
BUCKET = 'test_repository_integration'


class TestRepositoryIntegration(unittest.TestCase):
    def setUp(self):
        self.repo = Repository(MongoClient(HOST, PORT)[DB_NAME][BUCKET])
        self.mongo_collection = MongoClient(HOST, PORT)[DB_NAME][BUCKET]

    def tearDown(self):
        self.mongo_collection.drop()

    def test_save(self):
        thing_to_save = {'name': 'test_document'}
        another_thing_to_save = {'name': '2nd_test_document'}

        self.repo.save(thing_to_save)
        self.repo.save(another_thing_to_save)

        results = self.mongo_collection.find()
        assert_that(results, has_item(thing_to_save))
        assert_that(results, has_item(another_thing_to_save))

    def test_save_updates_document_with_id(self):
        a_document = { "_id": "event1", "title": "I'm an event"}
        updated_document = {"_id": "event1", "title": "I'm another event"}

        self.repo.save(a_document)
        self.repo.save(updated_document)

        saved_documents = self.mongo_collection.find()

        assert_that( saved_documents, only_contains(updated_document) )

    def test_find(self):
        self.mongo_collection.save({"name": "George", "plays": "guitar"})
        self.mongo_collection.save({"name": "John", "plays": "guitar"})
        self.mongo_collection.save({"name": "Paul", "plays": "bass"})
        self.mongo_collection.save({"name": "Ringo", "plays": "drums"})

        results = self.repo.find({"plays": "guitar"})

        assert_that(results, only_contains(
            has_entries({"name": "George", "plays": "guitar"}),
            has_entries({"name": "John", "plays": "guitar"}),
        ))

    def test_group(self):
        self.mongo_collection.save({"name": "George", "plays": "guitar"})
        self.mongo_collection.save({"name": "John", "plays": "guitar"})
        self.mongo_collection.save({"name": "Paul", "plays": "bass"})
        self.mongo_collection.save({"name": "Ringo", "plays": "drums"})

        results = self.repo.group("plays", {})

        assert_that(results, only_contains(
            has_entries({"plays": "guitar", "count": 2}),
            has_entries({"plays": "bass", "count": 1}),
            has_entries({"plays": "drums", "count": 1})
        ))

    def test_group_with_query(self):
        self.mongo_collection.save({"value": '1', "suite": "hearts"})
        self.mongo_collection.save({"value": '1', "suite": "diamonds"})
        self.mongo_collection.save({"value": '1', "suite": "clubs"})
        self.mongo_collection.save({"value": 'K', "suite": "hearts"})
        self.mongo_collection.save({"value": 'K', "suite": "diamonds"})

        results = self.repo.group("value", {"suite": "diamonds"})

        assert_that(results, only_contains(
            {"value": "1", "count": 1},
            {"value": "K", "count": 1}
        ))

    def test_grouping_by_multiple_keys(self):
        self.mongo_collection.save({"value": '1',
                                    "suite": "hearts",
                                    "hand": 1})
        self.mongo_collection.save({"value": '1',
                                    "suite": "diamonds",
                                    "hand": 1})
        self.mongo_collection.save({"value": '1',
                                    "suite": "clubs",
                                    "hand": 1})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "hearts",
                                    "hand": 1})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "diamonds",
                                    "hand": 1})

        self.mongo_collection.save({"value": '1',
                                    "suite": "hearts",
                                    "hand": 2})
        self.mongo_collection.save({"value": '1',
                                    "suite": "diamonds",
                                    "hand": 2})
        self.mongo_collection.save({"value": '1',
                                    "suite": "clubs",
                                    "hand": 2})
        self.mongo_collection.save({"value": 'K',
                                    "suite": "hearts",
                                    "hand": 2})
        self.mongo_collection.save({"value": 'Q',
                                    "suite": "diamonds",
                                    "hand": 2})

        result = self.repo.multi_group(["value", "suite"], {})

        assert_that(result, has_items(
            {
                "1": {
                    "hearts": {
                        "count": 2.0
                    },
                    "clubs": {
                        "count": 2.0
                    },
                    "diamonds": {
                        "count": 2.0
                    }
                    }
            },
            {
                "Q": {
                    "diamonds": {
                        "count": 1.0
                    }
                }
            },
            {
                "K": {
                    "hearts": {
                        "count": 2.0
                    },
                    "diamonds": {
                        "count": 1.0
                    }
                }
            }
        ))

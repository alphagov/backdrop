import unittest
from hamcrest import *
from backdrop.core import storage
from backdrop.core.records import Record


class TestMongoIntegration(unittest.TestCase):
    def setUp(self):
        self.store = storage.Store('localhost', 27017, 'backdrop_test')
        self.bucket = storage.Bucket(self.store, 'my_bucket')

    def tearDown(self):
        self.store.client.drop_database('backdrop_test')

    def test_that_a_list_of_objects_get_stored(self):
        my_objects = [
            {"name": "Groucho"},
            {"name": "Harpo"},
            {"name": "Chico"}
        ]

        my_records = [Record(obj) for obj in my_objects]

        self.bucket.store(my_records)

        retrieved_objects = self.bucket.all()

        for r in retrieved_objects:
            assert_that(r['name'], is_in([n['name'] for n in my_objects]))
            assert_that(r, has_key('_id'))

    def test_object_with_id_is_updated(self):
        event = { "_id": "event1", "title": "I'm an event"}
        updated_event = {"_id": "event1", "title": "I'm another event"}

        self.bucket.store(Record(event))
        self.bucket.store(Record(updated_event))

        retrieved_objects = self.bucket.all()

        assert_that( retrieved_objects, only_contains(updated_event) )

    def test_stored_object_is_appended_to_bucket(self):
        event = {"title": "I'm an event"}
        another_event = {"title": "I'm another event"}

        self.bucket.store(Record(event))
        self.bucket.store(Record(another_event))

        retrieved_objects = self.bucket.all()

        assert_that( retrieved_objects, contains(event, another_event) )

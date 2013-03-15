import unittest
import datetime
from hamcrest import *
import pytz
from backdrop.core import storage
from backdrop.core.records import Record


def d(year, month, day, hour, minute, seconds):
    return datetime.datetime(year, month, day, hour, minute, seconds,
                             tzinfo=pytz.UTC)


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

        for r in retrieved_objects:
            assert_that(
                r['title'],
                is_in( [e['title'] for e in [event, another_event]])
            )

    def test_filter_by_query(self):
        my_objects = [
            {"name": "Groucho"},
            {"name": "Harpo"},
            {"name": "Chico"}
        ]

        my_records = [Record(obj) for obj in my_objects]

        self.bucket.store(my_records)
        query_result = self.bucket.query(filter_by=[['name', 'Chico']])
        assert_that(query_result, contains(has_entries({'name': equal_to('Chico')})))
        assert_that(query_result, is_not(has_item(has_entries({'name': equal_to('Harpo')}))))

    def test_group_by_query(self):
        my_objects = [
            {"name": "Max"},
            {"name": "Max"},
            {"name": "Max"},
            {"name": "Gareth"},
            {"name": "Gareth"}
        ]

        my_records = [Record(obj) for obj in my_objects]
        self.bucket.store(my_records)

        query_result = self.bucket.query(group_by = "name")
        assert_that(query_result, has_item(has_entries({'Max': equal_to(3)})))
        assert_that(query_result, has_item(has_entries({'Gareth': equal_to(2)})))

    def test_query_with_timestamps(self):
        my_objects = [
            {"_timestamp": d(2013, 1, 1, 12, 0, 0), "month": "Jan"},
            {"_timestamp": d(2013, 2, 1, 12, 0, 0), "month": "Feb"},
            {"_timestamp": d(2013, 3, 1, 12, 0, 0), "month": "Mar"},
            {"_timestamp": d(2013, 4, 1, 12, 0, 0), "month": "Apr"},
            {"_timestamp": d(2013, 5, 1, 12, 0, 0), "month": "May"}
        ]

        my_records = [Record(obj) for obj in my_objects]
        self.bucket.store(my_records)

        query_for_start_at = self.bucket.query(
            start_at = d(2013, 4, 1, 12, 0, 0)
        )
        assert_that(query_for_start_at,
                    has_item(has_entries({'month': equal_to("Apr")})))
        assert_that(query_for_start_at,
                    has_item(has_entries({'month': equal_to("May")})))
        assert_that(query_for_start_at,
                    is_not(has_item(has_entries({'month': equal_to("Mar")}))))

        query_for_end_at = self.bucket.query(
            end_at = d(2013, 4, 1, 12, 0, 0)
        )
        assert_that(query_for_end_at,
                    has_item(has_entries({'month': equal_to("Jan")})))
        assert_that(query_for_end_at,
                    has_item(has_entries({'month': equal_to("Feb")})))
        assert_that(query_for_end_at,
                    has_item(has_entries({'month': equal_to("Mar")})))
        assert_that(query_for_end_at,
                    is_not(has_item(has_entries({'month': equal_to("Apr")}))))

        query_for_start_and_end_at = self.bucket.query(
            end_at = d(2013, 3, 1, 12, 0, 0),
            start_at = d(2013, 2, 1, 12, 0, 0)
        )
        assert_that(query_for_start_and_end_at,
                    has_item(has_entries({'month': equal_to("Feb")})))
        assert_that(query_for_start_and_end_at,
                    is_not(has_item(has_entries({'month': equal_to("Jan")}))))
        assert_that(query_for_start_and_end_at,
                    is_not(has_item(has_entries({'month': equal_to("Mar")}))))

    def test_week_query(self):
        my_objects = [
            {'_timestamp': d(2013,1,7,0,0,0), 'release': '1'},
            {'_timestamp': d(2013,1,8,0,0,0), 'release': '2'},
            {'_timestamp': d(2013,1,9,0,0,0), 'release': '3'},
            {'_timestamp': d(2013,1,14,0,0,0), 'release': '4'},
        ]

        my_records = [Record(obj) for obj in my_objects]
        self.bucket.store(my_records)

        query_result = self.bucket.query(period='week')
        assert_that(query_result, has_length(2))

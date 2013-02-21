import os
import unittest
from dateutil import parser

from flask import json
import pytz

import api

DATABASE_NAME = "performance_platform_test"


def load_fixture(collection_name, fixture_name):
    root_path = os.path.join(os.path.dirname(__file__), '..', '..')
    fixture_path = os.path.join(root_path, 'test', 'data', fixture_name)
    with open(fixture_path) as fixture:
        for document in json.load(fixture):
            if "_timestamp" in document:
                document["_timestamp"] = parser.parse(document["_timestamp"]).astimezone(pytz.utc)
            api.mongo[DATABASE_NAME][collection_name].save(document)


class MyFlaskTestCase(unittest.TestCase):
    def setUp(self):
        api.app.config['DATABASE_NAME'] = DATABASE_NAME
        load_fixture('licencing', "licence.json")
        self.app = api.app.test_client()

#    def tearDown(self):
#        api.mongo[DATABASE_NAME]['licencing'].drop()

    def test_that_with_no_arguments_all_documents_are_returned(self):
        response = self.app.get('/licencing')

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.data)

        self.assertEqual(len(response_data['data']), 3)

    def test_that_events_later_than_start_at_are_returned(self):
        response = self.app.get('/licencing?start_at=2012-12-12T01:01:02%2B00:00')

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.data)

        self.assertEqual(len(response_data['data']), 1)


    def test_that_events_equal_to_or_later_than_start_at_are_returned(self):
        response = self.app.get('/licencing?start_at=2012-12-13T01:01:01%2B00:00')

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.data)

        self.assertEqual(len(response_data['data']), 1)
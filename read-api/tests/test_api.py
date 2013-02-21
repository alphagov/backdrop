import os
import unittest

from pymongo import MongoClient
from flask import json

import api

DATABASE_NAME = "performance_platform_test"


def load_fixture(collection_name, fixture_name):
    root_path = os.path.join(os.path.dirname(__file__), '..', '..')
    fixture_path = os.path.join(root_path, 'test', 'data', fixture_name)
    with open(fixture_path) as fixture:
        for document in json.load(fixture):
            api.mongo[DATABASE_NAME][collection_name].save(document)


class MyFlaskTestCase(unittest.TestCase):
    def setUp(self):
        api.app.config['DATABASE_NAME'] = DATABASE_NAME
        load_fixture('licencing', "licence.json")
        self.app = api.app.test_client()

    def tearDown(self):
        api.mongo[DATABASE_NAME]['licencing'].drop()

    def test_that_with_no_arguments_all_documents_are_returned(self):
        response = self.app.get('/licencing')

        response_data = json.loads(response.data)

        self.assertEqual(len(response_data['data']), 3)

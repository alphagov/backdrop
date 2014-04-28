import unittest
from pymongo import MongoClient
from hamcrest import *

from backdrop.core import database, data_set
from backdrop.core.data_set import DataSetConfig
from migrations.lib.change_buckets_to_data_sets import up

HOSTS = ['localhost']
PORT = 27017
DB_NAME = 'backdrop'
DATA_SET = 'users'


class ChangeBucketsToDataSetTestCase(unittest.TestCase):
    def setUp(self):
        self.db = database.Database(HOSTS, PORT, DB_NAME)
        self.data_set = data_set.DataSet(
            self.db, DataSetConfig(DATA_SET, data_group="group", data_type="type", max_age_expected=1000))
        self.mongo_collection = MongoClient(HOSTS, PORT)[DB_NAME][DATA_SET]
        self.mongo_collection.drop()
        self.data_sets = [
            "carers_allowance_weekly_claims",
            "waste_carriers_registration_transactions_by_channel",
            "waste_carriers_registration_cost_per_transaction"
        ]
        self.mongo_collection.save({
            "_id": "person@digital.cabinet-office.gov.uk",
            "buckets": self.data_sets,
            "email": "person@digital.cabinet-office.gov.uk"
        })

    def tearDown(self):
        self.mongo_collection.drop()

    def test_that_buckets_changes_to_data_sets(self):
        up(self.db)
        users = self.db.get_repository('users').find({})
        assert_that(users.count(), is_(1))
        for user in users:
            assert_that("buckets" in user, is_(False))
            assert_that(user["data_sets"], is_(self.data_sets))

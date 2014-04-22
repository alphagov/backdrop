from base64 import b64encode, b64decode
import unittest
from hamcrest import *
from nose.tools import raises
from backdrop.core.data_set import DataSet, DataSetConfig
from backdrop.core.errors import ValidationError
from tests.core.test_data_set import mock_repository, mock_database


class TestDataSetAutoIdGeneration(unittest.TestCase):
    def setUp(self):
        self.mock_repository = mock_repository()
        self.mock_database = mock_database(self.mock_repository)

    def test_auto_id_for_a_single_field(self):
        objects = [{
            "abc": "def"
        }]

        config = DataSetConfig("data_set", data_group="group", data_type="type", auto_ids=["abc"])

        data_set = DataSet(self.mock_database, config)

        data_set.parse_and_store(objects)

        self.mock_repository.save.assert_called_once_with({
            "_id": b64encode("def"),
            "abc": "def"
        })

    def test_auto_id_generation(self):
        objects = [{
            "postcode": "WC2B 6SE",
            "number": "125",
            "name": "Aviation House"
        }]

        config = DataSetConfig("data_set", data_group="group", data_type="type", auto_ids=("postcode", "number"))

        data_set = DataSet(self.mock_database, config)

        data_set.parse_and_store(objects)

        self.mock_repository.save.assert_called_once_with({
            "_id": b64encode("WC2B 6SE.125"),
            "postcode": "WC2B 6SE",
            "number": "125",
            "name": "Aviation House"
        })

    def test_no_id_generated_if_auto_id_is_none(self):
        object = {
            "postcode": "WC2B 6SE",
            "number": "125",
            "name": "Aviation House"
        }

        config = DataSetConfig("data_set", data_group="group", data_type="type")

        data_set = DataSet(self.mock_database, config)

        data_set.parse_and_store([object])

        self.mock_repository.save.assert_called_once_with(object)

    @raises(ValidationError)
    def test_validation_error_if_auto_id_property_is_missing(self):
        objects = [{
            "postcode": "WC2B 6SE",
            "name": "Aviation House"
        }]

        config = DataSetConfig("data_set", data_group="group", data_type="type", auto_ids=("postcode", "number"))

        data_set = DataSet(self.mock_database, config)

        data_set.parse_and_store(objects)

    def test_auto_id_can_be_generated_from_a_timestamp(self):
        objects = [{
            "_timestamp": "2013-08-01T00:00:00+00:00",
            "foo": "bar"
        }]

        config = DataSetConfig("data_set", data_group="group", data_type="type", auto_ids=["_timestamp", "foo"])

        data_set = DataSet(self.mock_database, config)
        data_set.parse_and_store(objects)

        saved_object = self.mock_repository.save.call_args[0][0]

        assert_that(b64decode(saved_object['_id']),
                    is_("2013-08-01T00:00:00+00:00.bar"))

from base64 import b64encode, b64decode
import unittest
from hamcrest import *
from nose.tools import raises
from backdrop.core.bucket import Bucket
from backdrop.core.errors import ValidationError
from tests.core.test_bucket import mock_repository, mock_database


class TestBucketAutoIdGeneration(unittest.TestCase):
    def setUp(self):
        self.mock_repository = mock_repository()
        self.mock_database = mock_database(self.mock_repository)

    def test_auto_id_for_a_single_field(self):
        objects = [{
            "abc": "def"
        }]

        auto_id = ["abc"]

        bucket = Bucket(self.mock_database, "bucket", generate_id_from=auto_id)

        bucket.parse_and_store(objects)

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

        auto_id = ("postcode", "number")
        bucket = Bucket(self.mock_database, "bucket", generate_id_from=auto_id)

        bucket.parse_and_store(objects)

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

        bucket = Bucket(self.mock_database, "bucket", generate_id_from=None)

        bucket.parse_and_store([object])

        self.mock_repository.save.assert_called_once_with(object)

    @raises(ValidationError)
    def test_validation_error_if_auto_id_property_is_missing(self):
        objects = [{
            "postcode": "WC2B 6SE",
            "name": "Aviation House"
        }]

        auto_id = ("postcode", "number")
        bucket = Bucket(self.mock_database, "bucket", generate_id_from=auto_id)

        bucket.parse_and_store(objects)

    def test_auto_id_can_be_generated_from_a_timestamp(self):
        objects = [{
            "_timestamp": "2013-08-01T00:00:00+00:00",
            "foo": "bar"
        }]

        auto_id = ["_timestamp", "foo"]

        bucket = Bucket(self.mock_database, "bucket", generate_id_from=auto_id)
        bucket.parse_and_store(objects)

        saved_object = self.mock_repository.save.call_args[0][0]

        assert_that(b64decode(saved_object['_id']),
                    is_("2013-08-01T00:00:00+00:00.bar"))

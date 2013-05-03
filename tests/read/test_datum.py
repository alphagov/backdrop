import json
import unittest
from bson import ObjectId
import datetime
from hamcrest import *
from json import JSONEncoder
import pytz
from tests.support.test_helpers import d_tz, d


class DatumEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, Datum):
            return obj.datum
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


class Datum(object):
    def __init__(self, mongo_doc):
        if "_timestamp" in mongo_doc:
            mongo_doc["_timestamp"] = \
                mongo_doc["_timestamp"].replace(tzinfo=pytz.utc)
        self.datum = mongo_doc

    @classmethod
    def encoder(cls):
        return DatumEncoder


class TestDatum(unittest.TestCase):
    def test_datum_should_serialize_to_json(self):
        stub_doc = {"_id": ObjectId(oid="0" * 24)}
        assert_that(
            json.dumps(Datum(stub_doc), cls=Datum.encoder()),
            is_((''
                 '{'
                 '"_id": "000000000000000000000000"'
                 '}'
                 ''
            ))
        )

    def test_datum_should_serialize_to_json_with_timestamps(self):
        stub_doc = {
            "_id": ObjectId(oid="0" * 24),
            "_timestamp": d_tz(2013, 4, 1)
        }
        assert_that(
            json.dumps(Datum(stub_doc), cls=Datum.encoder()),
            is_((''
                 '{'
                 '"_id": "000000000000000000000000", '
                 '"_timestamp": "2013-04-01T00:00:00+00:00"'
                 '}'
                 ''
            ))
        )

    def test_datum_should_serialize_other_fields_to_strings(self):
        stub_doc = {
            "_id": ObjectId(oid="0" * 24),
            "_timestamp": d_tz(2013, 4, 1),
            "field_1": "foo",
            "field_2": "bar",
            "field_3": "zap"
        }

        json_string = json.dumps(Datum(stub_doc), cls=Datum.encoder())

        assert_that(
            json.loads(json_string),
            is_(json.loads(''
                           '{'
                           '"_id": "000000000000000000000000", '
                           '"_timestamp": "2013-04-01T00:00:00+00:00", '
                           '"field_1": "foo", '
                           '"field_2": "bar", '
                           '"field_3": "zap" '
                           '}'
                           '',
            ))
        )

    def test_timestamps_should_have_utc_timezones(self):
        stub_doc = {
            "_timestamp": d(2013, 5, 5)
        }

        assert_that(Datum(stub_doc).datum["_timestamp"].tzinfo, is_(pytz.UTC))

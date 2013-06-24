import unittest
import datetime

from hamcrest import *

from backdrop.core.errors import ParseError
from backdrop.core.records import Record, parse, add_id
from tests.support.test_helpers import d_tz


class TestParse(unittest.TestCase):
    def test__timestamp_is_parsed_to_datetime(self):
        record = parse({"_timestamp": "2012-12-12T00:00:00+00:00"})

        assert_that(isinstance(record.data['_timestamp'], datetime.datetime))

    def test_validation_error_is_raised_if_cannot_parse(self):
        self.assertRaises(ParseError, parse, {"_timestamp": "foobar"})


class TestRecord(unittest.TestCase):
    def test_creation(self):
        incoming_data = {'foo': 'bar', 'zap': 'pow'}
        some_record = Record(incoming_data)
        assert_that(some_record.data, has_key("foo"))
        assert_that(some_record.data, has_value("bar"))
        assert_that(some_record.data, has_key("zap"))
        assert_that(some_record.data, has_value("pow"))

    def test__timestamp_is_returned_as_datetime(self):
        incoming_data = {
            'foo': 'bar',
            '_timestamp': d_tz(
                2013, 2, 2, 0, 2, 0
            )
        }
        some_record = Record(incoming_data)

        assert_that(
            some_record.data['_timestamp'],
            is_(
                d_tz(2013, 2, 2, 0, 2, 0)
            )
        )

    def test_data_without__timestamp_does_not_get__period_start_ats(self):
        incoming_data = {"foo": "bar"}
        record = Record(incoming_data)

        assert_that(record.meta, is_not(has_key("_week_start_at")))
        assert_that(record.meta, is_not(has_key("_month_start_at")))

    def test_data_with__timestamp_gets_a__period_start_ats(self):
        incoming_data = {
            'foo': 'bar',
            '_timestamp': d_tz(2013, 2, 2, 0, 0, 0)
        }
        some_record = Record(incoming_data)

        assert_that(
            some_record.meta["_week_start_at"],
            is_(d_tz(2013, 1, 28))
        )

        assert_that(
            some_record.meta["_month_start_at"],
            is_(d_tz(2013, 2, 1))
        )

    def test__week_start_at_is_always_the_start_of_the_week(self):
        incoming_data_1 = {
            'foo': 'bar',
            '_timestamp': d_tz(2013, 2, 7)
        }
        incoming_data_2 = {
            'foo': 'bar',
            '_timestamp': d_tz(2013, 3, 14)
        }
        record_1 = Record(incoming_data_1)
        record_2 = Record(incoming_data_2)

        assert_that(
            record_1.meta["_week_start_at"],
            is_(d_tz(2013, 2, 4))
        )
        assert_that(
            record_2.meta["_week_start_at"],
            is_(d_tz(2013, 3, 11))
        )

    def test__month_start_at_is_always_the_start_of_the_month(self):
        incoming_data_1 = {
            'foo': 'bar',
            '_timestamp': d_tz(2013, 2, 7)
        }
        incoming_data_2 = {
            'foo': 'bar',
            '_timestamp': d_tz(2013, 3, 14)
        }
        record_1 = Record(incoming_data_1)
        record_2 = Record(incoming_data_2)

        assert_that(
            record_1.meta["_month_start_at"],
            is_(d_tz(2013, 2, 1))
        )
        assert_that(
            record_2.meta["_month_start_at"],
            is_(d_tz(2013, 3, 1))
        )

    def test__period_start_ats_get_time_zeroed(self):
        incoming_data = {
            'foo': 'bar',
            '_timestamp': d_tz(2013, 2, 7, 7, 7, 7)
        }
        meta_info = Record(incoming_data).meta

        assert_that(meta_info['_week_start_at'].time(),
                    equal_to(datetime.time(0, 0, 0)))
        assert_that(meta_info['_month_start_at'].time(),
                    equal_to(datetime.time(0, 0, 0)))

    def test_equality(self):
        assert_that(Record({'foo': 1}), is_(equal_to(Record({'foo': 1}))))

    def test_to_mongo(self):
        record = Record({
            'name': 'bob',
            '_timestamp': d_tz(2013, 4, 4, 4, 4, 4)
        })

        assert_that(record.to_mongo(), has_key('name'))
        assert_that(record.to_mongo(), has_key('_timestamp'))
        assert_that(record.to_mongo(), has_key('_week_start_at'))


class TestAddId(unittest.TestCase):
    def test_adds_id_to_record(self):
        record = {
            "start_at": "2013-01-01",
            "end_at": "2013-01-07",
            "key": "record-key",
            "other_property": 123
        }

        modified_record = add_id(record)

        assert_that(modified_record, has_entries(record))
        assert_that(modified_record,
                    has_entry("_id", "record-key.2013-01-01.2013-01-07"))

    def test_does_not_change_record_already_with_id(self):
        record = {
            "_id": 1,
            "start_at": "2013-01-01",
            "end_at": "2013-01-07",
            "key": "record-key",
            "other_property": 123
        }

        modified_record = add_id(record)

        assert_that(modified_record, equal_to(record))

    def test_does_not_change_record_without_required_properties(self):
        record = {
            "name": "Guido",
            "preferred_language": "python"
        }

        modified_record = add_id(record)

        assert_that(modified_record, equal_to(record))

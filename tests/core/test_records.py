import unittest
import datetime

from hamcrest import *
import pytz

from backdrop.core.records import Record, parse
from backdrop.core.validation import ValidationError


class TestParse(unittest.TestCase):
    def test__timestamp_is_parsed_to_datetime(self):
        record = parse({"_timestamp": "2012-12-12T00:00:00+00:00"})

        assert_that(isinstance(record.data['_timestamp'], datetime.datetime))

    def test_validation_error_is_raised_if_cannot_parse(self):
        self.assertRaises(ValidationError, parse, {"_timestamp": "foobar"})


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
            '_timestamp': datetime.datetime(
                2013, 2, 2, 0, 2, 0,
                tzinfo=pytz.UTC
            )
        }
        some_record = Record(incoming_data)

        assert_that(
            some_record.data['_timestamp'],
            is_(instance_of(datetime.datetime))
        )
        assert_that(
            some_record.data['_timestamp'],
            is_(
                datetime.datetime(2013, 2, 2, 0, 2, 0, tzinfo=pytz.UTC)
            )
        )

    def test_data_without__timestamp_does_not_get__week_start_at(self):
        incoming_data = {"foo": "bar"}
        record = Record(incoming_data)

        assert_that(record.meta, is_not(has_key("_week_start_at")))

    def test_data_with__timestamp_gets_a__week_start_at(self):
        incoming_data = {
            'foo': 'bar',
            '_timestamp': datetime.datetime(2013, 2, 2, 0, 0, 0,
                                            tzinfo=pytz.UTC)
        }
        some_record = Record(incoming_data)

        assert_that(some_record.meta, has_key("_week_start_at"))
        assert_that(
            some_record.meta["_week_start_at"],
            is_(datetime.datetime(2013, 1, 28, tzinfo=pytz.UTC))
        )

    def test__week_start_at_is_always_a_week_before__timestamp(self):
        incoming_data_1 = {
            'foo': 'bar',
            '_timestamp': datetime.datetime(2013, 2, 7, 0, 0, 0,
                                            tzinfo=pytz.UTC)
        }
        incoming_data_2 = {
            'foo': 'bar',
            '_timestamp': datetime.datetime(2013, 3, 14, 0, 0, 0,
                                            tzinfo=pytz.UTC)
        }
        record_1 = Record(incoming_data_1)
        record_2 = Record(incoming_data_2)

        assert_that(
            record_1.meta["_week_start_at"],
            is_(datetime.datetime(2013, 2, 4, tzinfo=pytz.UTC))
        )
        assert_that(
            record_2.meta["_week_start_at"],
            is_(datetime.datetime(2013, 3, 11, tzinfo=pytz.UTC))
        )

    def test__week_start_at_gets_time_zeroed(self):
        incoming_data = {
            'foo': 'bar',
            '_timestamp': datetime.datetime(2013, 2, 7, 7, 7, 7,
                                            tzinfo=pytz.UTC)
        }
        meta_info = Record(incoming_data).meta
        assert_that(meta_info['_week_start_at'].hour, is_(0))
        assert_that(meta_info['_week_start_at'].minute, is_(0))
        assert_that(meta_info['_week_start_at'].second, is_(0))

    def test_equality(self):
        assert_that(Record({'foo': 1}), is_(equal_to(Record({'foo': 1}))))

    def test_to_mongo(self):
        record = Record({
            'name': 'bob',
            '_timestamp': datetime.datetime(2013, 4, 4, 4, 4, 4,
                                            tzinfo=pytz.UTC)
        })

        assert_that(record.to_mongo(), has_key('name'))
        assert_that(record.to_mongo(), has_key('_timestamp'))
        assert_that(record.to_mongo(), has_key('_week_start_at'))

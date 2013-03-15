import unittest
import datetime
from hamcrest import *
import pytz
from mock import patch, Mock
from backdrop.core import records
from backdrop.core.records import Record


class IncomingDataToRecordsParserTestCase(unittest.TestCase):
    def test_that_a_record_gets_created(self):
        data = {'foo': 'bar'}
        record = records.parse(data)
        assert_that(record, is_(instance_of(Record)))
        assert_that(record.data, has_entries({'foo': equal_to('bar')}))

    @patch('backdrop.core.records.Record')
    def test_that__timestamp_gets_parsed_to_a_datetime(self, mock_Record):
        data = {
            'zap': 'pow',
            '_timestamp': '2013-03-15T11:40:00+00:00'
        }
        records.parse(data)
        mock_Record.assert_called_with({
            'zap': 'pow',
            '_timestamp': datetime.datetime(2013, 3, 15, 11, 40, 0,
                                            tzinfo=pytz.UTC)
        })

import datetime
import unittest

from hamcrest import assert_that, is_
from mock import patch

from backdrop.write.api import bounding_dates, trigger_transforms


class BoundingDatesTestCase(unittest.TestCase):

    def test_bounding_dates(self):
        data = [
            {'_timestamp': datetime.datetime(2014, 9, 3)},
            {'_timestamp': datetime.datetime(2014, 9, 9)},
            {'_timestamp': datetime.datetime(2014, 9, 7)},
            {'_timestamp': datetime.datetime(2014, 9, 1)},
        ]

        earliest, latest = bounding_dates(data)

        assert_that(earliest.day, is_(1))
        assert_that(latest.day, is_(9))


class TriggerTransformsTestCase(unittest.TestCase):

    @patch('backdrop.write.api.celery_app')
    def test_trigger_transforms(self, mock_celery_app):
        earliest = datetime.datetime(2014, 9, 3)
        latest = datetime.datetime(2014, 9, 10)
        data = [
            {'_timestamp': earliest},
            {'_timestamp': latest},
        ]

        trigger_transforms({'name': 'dataset'}, data)

        mock_celery_app.send_task.assert_called_with(
            'backdrop.transformers.dispatch.entrypoint',
            args=('dataset', earliest, latest))

    @patch('backdrop.write.api.celery_app')
    def test_trigger_transforms_no_data(self, mock_celery_app):
        trigger_transforms({'name': 'dataset'}, [])
        assert_that(mock_celery_app.send_task.called, is_(False))

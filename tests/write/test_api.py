import datetime
import json
import unittest
import pytz

from hamcrest import assert_that, is_
from mock import patch

from backdrop.write import api
from backdrop.write.api import bounding_dates, trigger_transforms, parse_bounding_dates

from tests.support.performanceplatform_client import fake_data_set_exists, fake_no_data_sets_exist
from tests.support.test_helpers import is_ok


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


class ParseBoundingDatesTestCase(unittest.TestCase):
    def setUp(self):
        self.data = {
            "_start_at": "2014-12-17T00:00:00Z",
            # _end_at omitted so that it's generated
        }

    def test_end_at_has_no_microseconds_when_generated(self):
        _, latest = parse_bounding_dates(self.data)

        assert_that(latest.microsecond, is_(0))

    def test_end_at_has_utc_timezone_when_generated(self):
        _, latest = parse_bounding_dates(self.data)

        assert_that(latest.tzinfo, is_(pytz.UTC))


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

    @patch('backdrop.write.api.celery_app')
    def test_trigger_transforms_with_dates(self, mock_celery_app):
        earliest = datetime.datetime(2014, 9, 3)
        latest = datetime.datetime(2014, 9, 10)

        trigger_transforms(
            {'name': 'dataset'},
            earliest=earliest,
            latest=latest
        )

        mock_celery_app.send_task.assert_called_with(
            'backdrop.transformers.dispatch.entrypoint',
            args=('dataset', earliest, latest))


class TriggerTransformsEndpointTestCase(unittest.TestCase):

    def setUp(self):
        self.app = api.app.test_client()

    @fake_data_set_exists("foo", data_group="some-group", data_type="some-type", bearer_token="foo-bearer-token")
    def test_endpoint_succeeds(self):

        data = json.dumps({
            "_start_at": "2014-12-17T00:00:00Z",
        })

        response = self.app.post(
            '/data/some-group/some-type/transform',
            data=data,
            content_type='application/json',
            headers=[('Authorization', 'Bearer foo-bearer-token')],
        )
        assert_that(response, is_ok())

    @fake_data_set_exists("foo", data_group="some-group", data_type="some-type", bearer_token="foo-bearer-token")
    @patch('backdrop.write.api.trigger_transforms')
    def test_endpoint_triggers_task(self, mock_trigger_transforms):

        earliest = datetime.datetime(2014, 12, 17, 0, 0)
        latest = datetime.datetime(2014, 12, 18, 0, 0)
        data = json.dumps({
            "_start_at": str(earliest),
            "_end_at": str(latest),
        })

        self.app.post(
            '/data/some-group/some-type/transform',
            data=data,
            content_type='application/json',
            headers=[('Authorization', 'Bearer foo-bearer-token')],
        )
        mock_trigger_transforms.assert_called_with({'bearer_token': 'foo-bearer-token',
                                                    'capped_size': 0,
                                                    'name': 'foo',
                                                    'data_type': 'some-type',
                                                    'data_group': 'some-group'},
                                                   earliest=earliest,
                                                   latest=latest)

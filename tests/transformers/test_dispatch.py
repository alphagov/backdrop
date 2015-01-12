import pytz
import unittest

from datetime import datetime
from hamcrest import assert_that, is_, has_entries, equal_to
from mock import patch, MagicMock

from backdrop.transformers.dispatch import (
    entrypoint,
    run_transform,
    get_query_parameters,
    get_or_get_and_create_output_dataset
)


class DispatchTestCase(unittest.TestCase):

    @patch('backdrop.transformers.dispatch.AdminAPI')
    @patch('backdrop.transformers.dispatch.app')
    def test_entrypoint(self, mock_app, mock_adminAPI):
        adminAPI_instance = mock_adminAPI.return_value
        adminAPI_instance.get_data_set_transforms.return_value = [
            {'type': 1}, {'type': 2}
        ]
        adminAPI_instance.get_data_set_by_name.return_value = {
            "group": "foo",
            "type": "bar",
        }

        earliest = datetime(2014, 12, 10, 12, 00, 00, tzinfo=pytz.utc)
        latest = datetime(2014, 12, 14, 12, 00, 00, tzinfo=pytz.utc)
        entrypoint('dataset123', earliest, latest)

        assert_that(mock_app.send_task.call_count, is_(2))
        mock_app.send_task.assert_any_call(
            'backdrop.transformers.dispatch.run_transform',
            args=(
                {"group": "foo", "type": "bar"},
                {'type': 1},
                earliest,
                latest))
        mock_app.send_task.assert_any_call(
            'backdrop.transformers.dispatch.run_transform',
            args=(
                {"group": "foo", "type": "bar"},
                {'type': 2},
                earliest,
                latest))

    @patch('backdrop.transformers.dispatch.AdminAPI')
    @patch('backdrop.transformers.dispatch.DataSet')
    @patch('backdrop.transformers.tasks.debug.logging')
    def test_run_transform(
            self,
            mock_logging_task,
            mock_data_set,
            mock_adminAPI):
        mock_logging_task.return_value = [{'new-data': 'point'}]
        adminAPI_instance = mock_adminAPI.return_value
        adminAPI_instance.get_data_set.return_value = {
            "bearer_token": "foo2",
        }
        data_set_instance = MagicMock()
        data_set_instance.get.return_value = {
            'data': [
                {'data': 'point'},
            ],
        }
        mock_data_set.from_group_and_type.return_value = data_set_instance

        earliest = datetime(2014, 12, 10, 12, 00, 00, tzinfo=pytz.utc)
        latest = datetime(2014, 12, 14, 12, 00, 00, tzinfo=pytz.utc)

        run_transform({
            'data_group': 'group',
            'data_type': 'type',
            'token': 'foo',
        }, {
            'type': {
                'function': 'backdrop.transformers.tasks.debug.logging',
            },
            'query-parameters': {
                'period': 'day',
            },
            'options': {},
            'output': {
                'data-group': 'other-group',
                'data-type': 'other-type',
            },
        }, earliest, latest)

        mock_data_set.from_group_and_type.assert_any_call(
            'http://backdrop/data', 'group', 'type',
        )
        data_set_instance.get.assert_called_with(
            query_parameters={
                'period': 'day',
                'flatten': 'true',
                'start_at': '2014-12-10T12:00:00+00:00',
                'end_at': '2014-12-14T12:00:00+00:00',
            },
        )
        mock_logging_task.assert_called_with(
            [{'data': 'point'}],
            {}
        )
        mock_data_set.from_group_and_type.assert_any_call(
            'http://backdrop/data', 'other-group', 'other-type', token='foo2',
        )
        data_set_instance.post.assert_called_with([{'new-data': 'point'}])

    @patch('backdrop.transformers.dispatch.AdminAPI')
    @patch('backdrop.transformers.dispatch.DataSet')
    @patch('backdrop.transformers.tasks.debug.logging')
    def test_run_transform_no_output_group(
            self,
            mock_logging_task,
            mock_data_set,
            mock_adminAPI):
        mock_logging_task.return_value = [{'new-data': 'point'}]
        adminAPI_instance = mock_adminAPI.return_value
        adminAPI_instance.get_data_set.return_value = {
            "bearer_token": "foo2",
        }
        data_set_instance = MagicMock()
        data_set_instance.get.return_value = {
            'data': [
                {'data': 'point'},
            ],
        }
        mock_data_set.from_group_and_type.return_value = data_set_instance

        earliest = datetime(2014, 12, 10, 12, 00, 00, tzinfo=pytz.utc)
        latest = datetime(2014, 12, 14, 12, 00, 00, tzinfo=pytz.utc)

        run_transform({
            'data_group': 'group',
            'data_type': 'type',
            'bearer_token': 'foo',
        }, {
            'type': {
                'function': 'backdrop.transformers.tasks.debug.logging',
            },
            'query-parameters': {
                'period': 'day',
            },
            'options': {},
            'output': {
                'data-type': 'other-type',
            },
        }, earliest, latest)

        mock_data_set.from_group_and_type.assert_any_call(
            'http://backdrop/data', 'group', 'other-type', token='foo2',
        )

    @patch('backdrop.transformers.dispatch.AdminAPI')
    @patch('backdrop.transformers.dispatch.DataSet')
    def test_get_or_get_and_create_dataset_when_data_set_exists(
            self,
            mock_data_set,
            mock_adminAPI):
        transform_config = {
            'output': {
                'data-group': 'floop',
                'data-type': 'wibble'
            }
        }
        input_dataset_config = {
            "bearer_token": "foo2",
            'data_group': 'loop',
            'data_type': 'flibble'
        }
        adminAPI_instance = mock_adminAPI.return_value
        adminAPI_instance.get_data_set.return_value = {
            "bearer_token": "foo2",
        }
        data_set_instance = MagicMock()
        data_set_instance.get.return_value = {
            'data': [
                {'data': 'point'},
            ],
        }
        mock_data_set.from_group_and_type.return_value = data_set_instance

        output_data_set = get_or_get_and_create_output_dataset(
            transform_config,
            input_dataset_config)
        assert_that(output_data_set, equal_to(data_set_instance))
        adminAPI_instance.get_data_set.assert_called_once_with(
            'floop',
            'wibble'
        )
        mock_data_set.from_group_and_type.assert_called_once_with(
            'http://backdrop/data', 'floop', 'wibble', token='foo2',
        )

    @patch('backdrop.transformers.dispatch.AdminAPI')
    @patch('backdrop.transformers.dispatch.DataSet')
    def test_get_and_get_or_create_dataset_when_get_finds_nothing(
            self,
            mock_data_set,
            mock_adminAPI):
        transform_config = {
            'output': {
                'data-group': 'floop',
                'data-type': 'wibble'
            }
        }
        input_dataset_config = {
            "bearer_token": "foo2",
            'data_group': 'loop',
            'data_type': 'flibble'
        }
        adminAPI_instance = mock_adminAPI.return_value
        adminAPI_instance.get_data_set.return_value = None
        adminAPI_instance = mock_adminAPI.return_value
        adminAPI_instance.create_data_set.return_value = {
            'bearer_token': 'foo2',
            'data_group': 'floop',
            'data_type': 'wibble'
        }
        data_set_instance = MagicMock()
        data_set_instance.get.return_value = {
            'data': [
                {'data': 'point'},
            ],
        }
        mock_data_set.from_group_and_type.return_value = data_set_instance

        output_data_set = get_or_get_and_create_output_dataset(
            transform_config,
            input_dataset_config)
        assert_that(output_data_set, equal_to(data_set_instance))
        adminAPI_instance.create_data_set.assert_called_once_with({
            'data_group': 'floop',
            'data_type': 'wibble',
            'bearer_token': 'foo2'
        })
        mock_data_set.from_group_and_type.assert_called_once_with(
            'http://backdrop/data', 'floop', 'wibble', token='foo2',
        )


class GetQueryParametersTestCase(unittest.TestCase):

    def test_same_timestamps_period(self):
        earliest = datetime(2014, 12, 14, 12, 00, 00, tzinfo=pytz.utc)
        latest = datetime(2014, 12, 14, 12, 00, 00, tzinfo=pytz.utc)
        transform = {
            'query-parameters': {
                'period': 'week',
            }
        }

        query_parameters = get_query_parameters(transform, earliest, latest)

        assert_that(query_parameters, has_entries({
            'period': 'week',
            'duration': 1,
            'start_at': '2014-12-14T12:00:00+00:00',
        }))

    def test_same_timestamps_non_period(self):
        earliest = datetime(2014, 12, 14, 12, 00, 00, tzinfo=pytz.utc)
        latest = datetime(2014, 12, 14, 12, 00, 00, tzinfo=pytz.utc)
        transform = {
            'query-parameters': {
            }
        }

        query_parameters = get_query_parameters(transform, earliest, latest)

        assert_that(query_parameters, has_entries({
            'start_at': '2014-12-14T12:00:00+00:00',
            'end_at': '2014-12-14T12:00:00+00:00',
            'inclusive': 'true',
        }))

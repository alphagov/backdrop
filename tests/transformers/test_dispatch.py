import unittest

from hamcrest import assert_that, is_
from mock import patch, MagicMock

from backdrop.transformers.dispatch import entrypoint, run_transform


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

        entrypoint('dataset123', 'earliest', 'latest')

        assert_that(mock_app.send_task.call_count, is_(2))
        mock_app.send_task.assert_any_call(
            'backdrop.transformers.dispatch.run_transform',
            args=({"group": "foo", "type": "bar"}, {'type': 1}, 'earliest', 'latest'))
        mock_app.send_task.assert_any_call(
            'backdrop.transformers.dispatch.run_transform',
            args=({"group": "foo", "type": "bar"}, {'type': 2}, 'earliest', 'latest'))

    @patch('backdrop.transformers.dispatch.DataSet')
    def test_run_transform(self, mock_data_set):
        data_set_instance = MagicMock()
        mock_data_set.from_group_and_type.return_value = data_set_instance

        run_transform({
            'data_group': 'group',
            'data_type': 'type',
        }, {
            'query-parameters': {
                'period': 'day',
            },
        }, 'earliest', 'latest')

        data_set_instance.get.assert_called_with(
            query_parameters={
                'period': 'day',
                'flatten': 'true',
                'start_at': 'earliest',
                'end_at': 'latest',
            },
        )

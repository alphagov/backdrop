import unittest

from hamcrest import assert_that, is_
from mock import patch

from backdrop.transformers.dispatch import entrypoint


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

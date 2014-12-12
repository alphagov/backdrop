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

        entrypoint('dataset123', 'earliest', 'latest')

        assert_that(mock_app.send_task.call_count, is_(2))
        mock_app.send_task.assert_any_call(
            'backdrop.transformers.dispatch.run_transform',
            args=('dataset123', {'type': 1}, 'earliest', 'latest'))
        mock_app.send_task.assert_any_call(
            'backdrop.transformers.dispatch.run_transform',
            args=('dataset123', {'type': 2}, 'earliest', 'latest'))

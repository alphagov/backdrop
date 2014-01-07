import io
import os
import unittest
import werkzeug.datastructures
from backdrop.admin.uploaded_file import UploadedFile
from mock import MagicMock


class FileUploadTestCase(unittest.TestCase):
    def _file_storage_wrapper(self, contents, server_filename='/tmp/uploaded_file',
                              browser_filename='browser_filename.txt', content_type=None, content_length=None):
        with open(server_filename, 'w') as f:
            f.write(contents)
        g = open(server_filename, 'r')

        storage = werkzeug.datastructures \
            .FileStorage(stream=g,
                         filename=browser_filename,
                         content_type=content_type,
                         content_length=content_length)
        return storage

    def _uploaded_file_wrapper(self, contents=None, fixture_name=None, is_virus=False):
        if contents is not None:
            upload = self._uploaded_file_from_contents(contents)
        elif fixture_name is not None:
            upload = self._uploaded_file_from_fixture(fixture_name)
        else:
            raise TypeError("Takes one of contents or fixture_name argument")

        upload._is_potential_virus = MagicMock(return_value=is_virus)

        return upload

    def _uploaded_file_from_contents(self, contents):
        return UploadedFile(
            self._file_storage_wrapper(
                contents=contents,
                browser_filename="file.txt"))

    def _uploaded_file_from_fixture(self, fixture_name):
        fixture_path = os.path.join('features', 'fixtures', fixture_name)
        with open(fixture_path) as f:
            return UploadedFile(
                self._file_storage_wrapper(
                    contents=f.read(),
                    browser_filename=fixture_name))

import io
import os
import unittest
import werkzeug.datastructures
from backdrop.write.uploaded_file import UploadedFile


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

    def _uploaded_file_wrapper(self, contents=None, fixture_name=None):
        if len([i for i in [contents, fixture_name] if i is not None]) != 1:
            raise TypeError("Takes one of contents or fixture_name argument")

        if contents is not None:
            server_filename = '/tmp/file.txt'
            file_storage = self._file_storage_wrapper(
                contents=contents,
                server_filename=server_filename)

            upload = UploadedFile(
                file_storage,
                server_filename
            )
            return upload

        elif fixture_name is not None:
            full_filename = fixture_path = os.path.join('features', 'fixtures', fixture_name)
            with open(full_filename, 'rb') as f:
                file_storage = self._file_storage_wrapper(
                    contents=f.read(),
                    server_filename=full_filename)
            upload = UploadedFile(
                file_storage,
                full_filename  # server filename
            )
            return upload

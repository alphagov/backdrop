import io
import unittest
import werkzeug.datastructures


class FileUploadTestCase(unittest.TestCase):
    def _file_storage_wrapper(self, contents, filename="test", content_type=None, content_length=None):
        stream = io.StringIO(initial_value=unicode(contents))
        storage = werkzeug.datastructures \
            .FileStorage(stream=stream, filename = filename,
                         content_type=content_type,
                         content_length=content_length)
        return storage

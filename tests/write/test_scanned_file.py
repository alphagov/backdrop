import unittest
from hamcrest import assert_that, is_
from mock import Mock
from backdrop.write.scanned_file import ScannedFile
import subprocess
import os
from tests.support.file_upload_test_case import FileUploadTestCase


class TestScannedFile(FileUploadTestCase):

    def setUp(self):
        self.file_object = self._file_storage_wrapper("This is a test", browser_filename="abc.txt")
        self.scanner = ScannedFile(self.file_object)

    def tearDown(self):
        try:
            os.remove('/tmp/abc.txt')
        except OSError:
            pass

    def test_has_virus_signature(self):
        self.scanner._virus_signature = True
        self.scanner._save_file_to_disk = Mock()
        self.scanner._scan_file = Mock()
        self.scanner._clean_up = Mock()
        assert_that(self.scanner.has_virus_signature, is_(True))
        self.scanner._save_file_to_disk.assert_called_once_with()
        self.scanner._scan_file.assert_called_once_with()
        self.scanner._clean_up.assert_called_once_with()

    def test_saving_a_file_to_disk(self):
        self.scanner._save_file_to_disk()
        assert_that(file('/tmp/abc.txt').read(), is_("This is a test"))

    def test_cleaning_up_after_scanning(self):
        self.file_object.save('/tmp/abc.txt')
        self.scanner._clean_up()
        assert_that(os.path.exists('/tmp/abc.txt'), is_(False))

    def test_scanning_a_file(self):
        self.scanner._clamscan = Mock(return_value=True)
        self.scanner._scan_file()
        assert_that(self.scanner._virus_signature, is_(True))
        self.scanner._clamscan.assert_called_once_with("/tmp/abc.txt")

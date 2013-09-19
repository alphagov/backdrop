import unittest
from hamcrest import assert_that, is_
from mock import Mock
from backdrop.write.scanned_file import ScannedFile 
import subprocess
import mock
from tests.support.file_upload_test_case import FileUploadTestCase

class TestScannedFile(FileUploadTestCase):

    #def test_save_file_to_disk
      #file_object = self._file_storage_wrapper("This is a test", "abc.txt")

    #def test_scan_file_and_clean_up

    def test_has_virus_signature(self):
        mock_call = mock.Mock(return_value = True)
        subprocess.call = mock_call
        scanner = ScannedFile("tmp/eicar.com")
        assert_that(scanner.has_virus_signature, is_(True))
        mock_call.assert_called_once_with(["clamscan", "tmp/eicar.com"])


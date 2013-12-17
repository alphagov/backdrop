from hamcrest import assert_that, is_
from mock import Mock, patch
from backdrop.write.uploaded_file import UploadedFile, FileUploadException
from backdrop.write.scanned_file import ScannedFile, VirusSignatureError
from tests.support.file_upload_test_case import FileUploadTestCase


class TestUploadedFile(FileUploadTestCase):
    def test_getting_a_file_stream(self):
        contents = 'This is a test'

        upload = self._uploaded_file_wrapper(contents)
        assert_that(upload.file_stream().read(), is_(contents))

    def test_files_under_1000000_octets_are_valid(self):
        csv_length_999999 = '\n'.join(['aa,bb,ccc' for i in range(100000)])
        upload = self._uploaded_file_wrapper(contents=csv_length_999999)

        assert_that(upload.valid, is_(True))

    def test_files_over_1000000_octets_are_not_valid(self):
        csv_length_1000009 = '\n'.join(['aa,bb,ccc' for i in range(100001)])
        upload = self._uploaded_file_wrapper(contents=csv_length_1000009)

        assert_that(upload.valid, is_(False))

    def test_saving_file(self):
        csv_contents = '\n'.join(['aa,bb,ccc' for i in range(100000)])
        upload = self._uploaded_file_wrapper(contents=csv_contents)
        bucket = Mock()
        parser = Mock()
        upload.perform_virus_scan = Mock()
        parser.return_value = csv_contents
        upload.save(bucket, parser)
        assert_that(parser.called, is_(True))
        bucket.parse_and_store.assert_called_with(csv_contents)

    def test_saving_invalid_file_should_throw_an_exception(self):
        upload = self._uploaded_file_wrapper(contents='')
        bucket = Mock()
        parser = Mock()
        self.assertRaises(FileUploadException, upload.save, bucket, parser)
        assert_that(bucket.called, is_(False))


class TestUploadedFileContentTypeValidation(FileUploadTestCase):
    def test_csv_uploads_are_valid(self):
        upload = self._uploaded_file_wrapper("This is a test")

        assert_that(upload.valid, is_(True))

    def test_json_uploads_are_valid(self):
        upload = self._uploaded_file_wrapper('{"This": "is a test"}')

        assert_that(upload.valid, is_(True))

    def test_xls_uploads_are_valid(self):
        upload = self._uploaded_file_wrapper(fixture_name='xlsfile.xls')
        assert_that(upload.valid, is_(True))

    def test_xlsx_spreadsheets_are_valid(self):

        upload = self._uploaded_file_wrapper(fixture_name='data.xlsx')
        assert_that(upload.valid, is_(True))

    def test_exe_files_are_not_valid(self):
        upload = self._uploaded_file_wrapper(fixture_name='donothing.exe')
        assert_that(upload.valid, is_(False))

    @patch('backdrop.write.scanned_file.ScannedFile.has_virus_signature')
    def test_perform_virus_scan(self, has_virus_signature):
        upload = self._uploaded_file_wrapper('[fake empty content]')
        has_virus_signature.return_value = True
        self.assertRaises(VirusSignatureError, upload.perform_virus_scan)

from hamcrest import assert_that, is_, equal_to
from mock import Mock, patch
from backdrop.admin.uploaded_file import UploadedFile, FileUploadError
from backdrop.admin.scanned_file import ScannedFile, VirusSignatureError
from tests.admin.support.file_upload_test_case import FileUploadTestCase


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

    def test_loading_file(self):
        csv_contents = '\n'.join(['aa,bb,ccc' for i in range(100000)])
        upload = self._uploaded_file_wrapper(contents=csv_contents)

        with upload.file_stream() as f:
            loaded_contents = f.read()

        assert_that(loaded_contents, equal_to(csv_contents))

    def test_loading_invalid_file_should_throw_an_exception(self):
        upload = self._uploaded_file_wrapper(contents='')
        self.assertRaises(FileUploadError, upload.file_stream)


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

    def test_perform_virus_scan(self):
        upload = self._uploaded_file_wrapper('[fake empty content]', is_virus=True)
        assert_that(upload.valid, is_(False))

from hamcrest import assert_that, is_
from mock import Mock, patch
from backdrop.write.uploaded_file import UploadedFile, FileUploadException
from backdrop.write.scanned_file import ScannedFile, VirusSignatureError
from tests.support.file_upload_test_case import FileUploadTestCase


class TestUploadedFile(FileUploadTestCase):
    def test_getting_a_file_stream(self):
        upload = UploadedFile(self._file_storage_wrapper("This is a test", ""))
        assert_that(upload.file_stream().read(), is_(u'This is a test'))

    def test_files_under_1000000_octets_are_valid(self):
        upload = UploadedFile(self._file_storage_wrapper(
            "foo",
            content_type="text/csv",
            content_length=999999))

        assert_that(upload.valid, is_(True))

    def test_files_over_1000000_octets_are_valid(self):
        upload = UploadedFile(self._file_storage_wrapper(
            "foo",
            content_type="text/csv",
            content_length=1000001))

        assert_that(upload.valid, is_(False))

    def test_saving_file(self):
        upload = UploadedFile(self._file_storage_wrapper(
            contents="some data",
            content_type="text/csv"
        ))
        bucket = Mock()
        parser = Mock()
        upload.perform_virus_scan = Mock()
        parser.return_value = "some data"
        upload.save(bucket, parser)
        assert_that(parser.called, is_(True))
        bucket.parse_and_store.assert_called_with("some data")

    def test_saving_invalid_file_should_throw_an_exception(self):
        upload = UploadedFile(self._file_storage_wrapper(
            contents="some content"
        ))
        bucket = Mock()
        parser = Mock()
        self.assertRaises(FileUploadException, upload.save, bucket, parser )
        assert_that(bucket.called, is_(False))

    def test_uploaded_file_must_have_a_file(self):
        storage = self._file_storage_wrapper("boo", filename=None)
        self.assertRaises(FileUploadException, UploadedFile, storage)


class TestUploadedFileContentTypeValidation(FileUploadTestCase):
    def test_csv_uploads_are_valid(self):
        upload = UploadedFile(self._file_storage_wrapper("This is a test",
                                                         content_type="text/csv"))

        assert_that(upload.valid, is_(True))

    def test_json_uploads_are_valid(self):
        upload = UploadedFile(self._file_storage_wrapper("This is a test",
                                                         content_type="application/json"))

        assert_that(upload.valid, is_(True))

    def test_excel_uploads_are_valid(self):
        upload = UploadedFile(self._file_storage_wrapper(
            "This is a test", filename="test",
            content_type="application/vnd.ms-excel"))

        assert_that(upload.valid, is_(True))

    def test_xlsx_spreadsheets_are_valid(self):
        upload = UploadedFile(self._file_storage_wrapper(
            "This is a test",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ))

        assert_that(upload.valid, is_(True))

    def test_exe_files_are_not_valid(self):
        upload = UploadedFile(
            self._file_storage_wrapper('foo', content_type="application/exe"))

        assert_that(upload.valid, is_(False))

    def test_files_with_no_content_type_are_invalid(self):
        upload = UploadedFile(
            self._file_storage_wrapper('foo', content_type=None))

        assert_that(upload.valid, is_(False))

    @patch('backdrop.write.scanned_file.ScannedFile.has_virus_signature')
    def test_perform_virus_scan(self, has_virus_signature):
        file_storage_wrapper = self._file_storage_wrapper('foo', content_type=None)
        upload = UploadedFile(file_storage_wrapper)
        has_virus_signature.return_value = True
        self.assertRaises(VirusSignatureError, upload.perform_virus_scan)

from backdrop.write.scanned_file import ScannedFile, VirusSignatureError
from backdrop import statsd

import mimetypes
import os
from os import SEEK_END


class FileUploadException(IOError):
    def __init__(self, message):
        self.message = message


def _size_of_file_on_disk(filename):
    return os.path.getsize(filename)


class UploadedFile(object):
    # This is ~ 1mb in octets
    MAX_FILE_SIZE = 1000000  # exclusive, so anything >= to this is invalid

    def __init__(self, file_storage, server_filename):
        self.file_storage = file_storage
        self.server_filename = server_filename
        # we don't trust the browser's content_length or content_type
        self.file_size = _size_of_file_on_disk(server_filename)
        self.guessed_mimetype, _ = mimetypes.guess_type(server_filename)

    def file_stream(self):
        return self.file_storage.stream

    def _is_empty(self):
        return self.file_size == 0

    def _is_too_big(self):
        return self.file_size >= self.MAX_FILE_SIZE

    def _is_strange_content_type(self):
        return self.guessed_mimetype not in [
            "text/plain",  # guess_type() says csv files are 'text/plain'
            "text/csv",
            "application/json",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ]

    @statsd.timer('uploaded_file.save')
    def save(self, bucket, parser):
        problems = []
        if self._is_empty():
            problems += ['file is empty']
        if self._is_too_big():
            problems += ['file too big ({})'.format(self.file_size)]
        if self._is_strange_content_type():
            problems += ['strange content type of {}'.format(
                self.guessed_mimetype)]
        if problems:
            raise FileUploadException('Invalid file upload {0} - {1}'.format(
                self.file_storage.filename,
                ' and '.join(problems)))
        self.perform_virus_scan()
        data = parser(self.file_stream())
        bucket.parse_and_store(data)

    @statsd.timer('uploaded_file.perform_virus_scan')
    def perform_virus_scan(self):
        if ScannedFile(self.file_storage).has_virus_signature:
            raise VirusSignatureError(
                'File {0} could not be uploaded as it may contain a virus.'
                .format(self.file_storage.filename))

    @property
    def valid(self):
        return not any(
            [
                self._is_empty(),
                self._is_too_big(),
                self._is_strange_content_type()
            ]
        )

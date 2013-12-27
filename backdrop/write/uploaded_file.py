from backdrop.write.scanned_file import ScannedFile, VirusSignatureError
from backdrop import statsd

import mimetypes
import os
from werkzeug.utils import secure_filename


class FileUploadError(IOError):
    def __init__(self, message):
        self.message = message


def _size_of_file_on_disk(filename):
    return os.path.getsize(filename)


class UploadedFile(object):
    # This is ~ 1mb in octets
    MAX_FILE_SIZE = 1000000  # exclusive, so anything >= to this is invalid

    def __init__(self, file_storage):
        self.server_filename = os.path.join(
            'tmp',
            secure_filename(file_storage.filename))
        self.file_storage = file_storage
        try:
            self.file_storage.save(self.server_filename)
        except IOError as e:
            raise FileUploadError(e.message)
        # we don't trust the browser's content_length or content_type
        self.file_size = _size_of_file_on_disk(self.server_filename)
        self.guessed_mimetype, _ = mimetypes.guess_type(self.server_filename)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        os.remove(self.server_filename)

    def file_stream(self):
        self.validate()
        return open(self.server_filename)

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

    @statsd.timer('uploaded_file._is_potential_virus')
    def _is_potential_virus(self):
        return ScannedFile(self.file_storage).has_virus_signature

    def validate(self):
        problems = []
        if self._is_empty():
            problems += ['file is empty']
        if self._is_too_big():
            problems += ['file too big ({})'.format(self.file_size)]
        if self._is_strange_content_type():
            problems += ['strange content type of {}'.format(
                self.guessed_mimetype)]
        if self._is_potential_virus():
            problems += ['file may contain a virus']
        if problems:
            raise FileUploadError('Invalid file upload {0} - {1}'.format(
                self.file_storage.filename,
                ' and '.join(problems)))

    @property
    def valid(self):
        return not any([
            self._is_empty(),
            self._is_too_big(),
            self._is_strange_content_type(),
            self._is_potential_virus()
        ])

from backdrop.write.scanned_file import ScannedFile, VirusSignatureError
from backdrop import statsd

import magic
from os import SEEK_END


class FileUploadException(IOError):
    def __init__(self, message):
        self.message = message


def _size_of_file_object(f):
    f.seek(0, SEEK_END)
    size = f.tell()
    f.seek(0)
    return size


class UploadedFile(object):
    # This is ~ 1mb in octets
    MAX_FILE_SIZE = 1000001

    def __init__(self, file_object):
        self.file_object = file_object
        if file_object.filename is None:
            raise FileUploadException('No file uploaded %s' % self.file_object)
        self.file_size = _size_of_file_object(file_object) # we don't trust the browser's content_length
        self.magic_mimetype = magic.from_buffer(file_object.read(), mime=True) # we don't trust the browser's content_type
        file_object.seek(0)

    def file_stream(self):
        return self.file_object.stream

    def _is_empty(self):
        return self.file_size == 0

    def _is_too_big(self):
        return self.file_size >= self.MAX_FILE_SIZE

    def _is_strange_content_type(self):
        return self.magic_mimetype not in [
            "text/plain", # magic (a wraper around unix's file command) tells us that csv files are 'text/plain'
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
            problems += ['strange content type of {}'.format(self.magic_mimetype)]
        if problems:
            self.file_stream().close()
            raise FileUploadException('Invalid file upload {0} - {1}'.format(
                    self.file_object.filename,
                    ' and '.join(problems)))
        self.perform_virus_scan()
        data = parser(self.file_stream())
        bucket.parse_and_store(data)
        self.file_stream().close()

    @statsd.timer('uploaded_file.perform_virus_scan')
    def perform_virus_scan(self):
        if ScannedFile(self.file_object).has_virus_signature:
            self.file_stream().close()
            raise VirusSignatureError(
                'File {0} could not be uploaded as it may contain a virus.'
                .format(self.file_object.filename))

    @property
    def valid(self):
        return not any([self._is_empty(), self._is_too_big(), self._is_strange_content_type()])

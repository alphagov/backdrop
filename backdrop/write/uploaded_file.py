class FileUploadException(IOError):
    def __init__(self, message):
        self.message = message


class UploadedFile(object):
    # This is ~ 1mb in octets
    MAX_FILE_SIZE = 1000001

    def __init__(self, file_object):
        self.file_object = file_object
        if file_object.filename is None:
            raise FileUploadException('No file uploaded %s' % self.file_object)

    def file_stream(self):
        return self.file_object.stream

    def _is_size_valid(self):
        return self.file_object.content_length < self.MAX_FILE_SIZE

    def _is_content_type_valid(self):
        return self.file_object.content_type in [
            "text/csv",
            "application/json",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ]

    def save(self, bucket, parser):
        if not self.valid:
            self.file_stream().close()
            raise FileUploadException('Invalid file upload %s' %
                                      self.file_object)
        data = parser(self.file_stream())
        bucket.parse_and_store(data)
        self.file_stream().close()

    @property
    def valid(self):
        return self._is_size_valid() and self._is_content_type_valid()

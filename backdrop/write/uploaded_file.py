class FileUploadException(IOError):
    pass


class UploadedFile(object):
    def __init__(self, file_object):
        self.file_object = file_object
        if file_object.filename is None:
            raise FileUploadException

    def content(self):
        return self.file_object.read()

    def _is_size_valid(self):
        return self.file_object.content_length < 1000001

    def _is_content_type_valid(self):
        return self.file_object.content_type in [
            "text/csv",
            "application/json",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ]

    @property
    def valid(self):
        return self._is_size_valid() and self._is_content_type_valid()

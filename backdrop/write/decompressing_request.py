import gzip

from flask import current_app, g, abort
from flask.wrappers import Request
from io import BytesIO


class DecompressingRequest(Request):
    """
    Subclass of flask.wrappers.Request which supports requests made with
    compressed requests bodies.

    See http://tools.ietf.org/html/rfc2616#section-14.11
    """

    def get_data(self, *args, **kwargs):
        """
        Override the get_data method to check whether the request entity
        was compressed. If it was, transparently decompress it and carry on.

        This is somewhat inefficient in that the entire entity is loaded
        into memory, rather than decorating the existing stream.
        """
        content_encoding = self.headers.get('content-encoding', '').lower()

        if (not g.get('_has_decompressed_entity', False)
                and 'gzip' in content_encoding):

            # Decompress the stream
            bytes = super(DecompressingRequest, self).get_data(*args, **kwargs)

            current_app.logger.debug("Got gzipped stream of length <%d>" %
                                     len(bytes))

            gzipped_content = BytesIO(bytes)

            decompressed_content = SafeGzipDecompressor(gzipped_content)

            data = decompressed_content.read().decode('utf-8')

            current_app.logger.debug("Got JSON of length <%s>" % (len(data)))

            # Store it on the _cached_data attribute for future reads
            self._cached_data = data

            g._has_decompressed_entity = True

        return super(DecompressingRequest, self).get_data(*args, **kwargs)


class SafeGzipDecompressor(object):
    """Class that decompresses gzip streams, and supports a maximum
    size to avoid zipbombs.

    See http://en.wikipedia.org/wiki/Zip_bomb
    """
    blocksize = 8 * 1024

    def __init__(self, fileobj, maxsize=10 * 1024 * 1024):
        self.maxsize = maxsize
        self.gzipobj = gzip.GzipFile(mode='rb', fileobj=fileobj)

    def read(self):
        b = [""]
        buf_size = 0
        while True:
            data = self.gzipobj.read(self.blocksize)
            if not data:
                break
            b.append(data)
            buf_size += len(data)

            if buf_size > self.maxsize:
                # Compressed file is too large
                abort(413)

        return "".join(b)

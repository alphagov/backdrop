import gzip

from flask import current_app, g
from flask.wrappers import Request
from io import BytesIO


class DecompressingRequest(Request):
    """
    Subclass of flask.wrappers.Request which supports requests made with
    compressed requests bodies.

    See http://tools.ietf.org/html/rfc2616#section-14.11
    """

    def get_data(self, cache=True, as_text=False, parse_form_data=False):
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
            bytes = super(DecompressingRequest, self).get_data(cache,
                                                               as_text,
                                                               parse_form_data)

            current_app.logger.debug("Got gzipped stream of length <%d>" %
                                     len(bytes))

            gzipped_content = BytesIO(bytes)

            decompressed_content = gzip.GzipFile(mode='rb',
                                                 fileobj=gzipped_content)

            data = decompressed_content.read().decode('utf-8')

            current_app.logger.debug("Got JSON of length <%s>" % (len(data)))

            # Store it on the _cached_data attribute for future reads
            self._cached_data = data

            g._has_decompressed_entity = True

        return super(DecompressingRequest, self).get_data(cache,
                                                          as_text,
                                                          parse_form_data)

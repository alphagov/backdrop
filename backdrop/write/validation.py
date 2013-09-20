from logging import getLogger

log = getLogger(__name__)


def extract_bearer_token(header):
    if header is None or len(header) < 8:
        return ''
        # Strip the leading "Bearer " from the header value
    return header[7:]


def bearer_token_is_valid(bucket, auth_header):

    request_token = extract_bearer_token(auth_header)

    if request_token != bucket.bearer_token:
        log.error("expected <%s> but was <%s>" % (
            bucket.bearer_token, request_token))
        return False
    return True

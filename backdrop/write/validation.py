from logging import getLogger

log = getLogger(__name__)


def bearer_token_is_valid(tokens, auth_header, bucket_name):
    def extract_bearer_token(header):
        if header is None or len(header) < 8:
            return ''
            # Strip the leading "Bearer " from the header value
        return header[7:]

    expected_token = tokens.get(bucket_name, None)
    request_token = extract_bearer_token(auth_header)

    if request_token != expected_token:
        log.error("expected <%s> but was <%s>" % (
            expected_token, request_token))
        return False
    return True

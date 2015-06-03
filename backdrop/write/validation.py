from logging import getLogger

log = getLogger(__name__)


def extract_bearer_token(auth_header):
    """
    >>> extract_bearer_token(u'Bearer some-token')
    u'some-token'
    >>> extract_bearer_token('Bearer ') is None
    True
    >>> extract_bearer_token('Something Else') is None
    True
    """
    prefix = 'Bearer '
    if auth_header is None or not auth_header.startswith(prefix):
        return None
    token = auth_header[len(prefix):]
    return token if len(token) else None


def auth_header_is_valid(data_set, auth_header):

    request_token = extract_bearer_token(auth_header)

    if request_token and request_token == data_set.get('bearer_token', None):
        return True
    log.error("expected <%s> but was <%s>" % (
        data_set['bearer_token'], request_token))
    return False

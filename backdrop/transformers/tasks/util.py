import base64


def encode_id(*parts):
    joined = '_'.join(parts)
    joined_bytes = joined.encode('utf-8')
    return base64.urlsafe_b64encode(joined_bytes)

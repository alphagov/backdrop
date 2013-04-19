from ..core.validation import valid, invalid, bucket_is_valid, key_is_valid,\
    value_is_valid, value_is_valid_datetime_string, value_is_valid_id,\
    key_is_reserved, key_is_internal


def validate_post_to_bucket(incoming_data, bucket_name):
    if not bucket_is_valid(bucket_name):
        return invalid('Bucket name is invalid')

    for datum in incoming_data:
        result = validate_data_object(datum)
        if not result.is_valid:
            return result

    return valid()


def validate_data_object(obj):
    for key, value in obj.items():
        if not key_is_valid(key):
            return invalid('{0} is not a valid key'.format(key))

        if key_is_internal(key) and not key_is_reserved(key):
            return invalid(
                '{0} is not a recognised internal field'.format(key))

        if not value_is_valid(value):
            return invalid('{0} has an invalid value'.format(key))

        if key == '_timestamp' and not value_is_valid_datetime_string(value):
            return invalid(
                '_timestamp is not a valid timestamp, it must be ISO8601')

        if key == '_id' and not value_is_valid_id(value):
            return invalid('_id is not a valid id')

    return valid()

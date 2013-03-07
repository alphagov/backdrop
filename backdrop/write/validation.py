from ..core.validation import valid, invalid, bucket_is_valid, key_is_valid,\
    value_is_valid, value_is_valid_datetime_string, value_is_valid_id


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

        if not value_is_valid(value):
            return invalid('{0} is not a valid value'.format(value))

        if key == '_timestamp' and not value_is_valid_datetime_string(value):
            return invalid('{0} is not a valid timestamp'.format(value))

        if key == '_id' and not value_is_valid_id(value):
            return invalid('{0} is not a valid _id'.format(value))

    return valid()

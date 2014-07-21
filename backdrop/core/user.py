def _data_set_list_is_valid(data_sets):
    if not isinstance(data_sets, list):
        return False

    is_string = lambda value: isinstance(value, basestring)

    return all(map(is_string, data_sets))

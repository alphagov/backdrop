from collections import namedtuple


def _data_set_list_is_valid(data_sets):
    if not isinstance(data_sets, list):
        return False

    is_string = lambda value: isinstance(value, basestring)

    return all(map(is_string, data_sets))


_UserConfig = namedtuple(
    "_UserConfig",
    "email data_sets")


class UserConfig(_UserConfig):
    def __new__(cls, email, data_sets=None):
        if data_sets is None:
            data_sets = []
        elif not _data_set_list_is_valid(data_sets):
            raise ValueError("data_sets must be a list of data_set names")

        return super(UserConfig, cls).__new__(cls, email, data_sets)

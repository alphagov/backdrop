from stagecraft import create_or_update_stagecraft_service


TEST_STAGECRAFT_PORT = 3204


def _get_user_routes(email, data):
    return {
        ('GET', u'users/{}'.format(email)): data,
        ('GET', u'users'): [data],
    }


def ensure_user_has_permissions(context, email, data_sets):
    user_data = {
        "email": email,
        "data_sets": data_sets
    }

    routes = _get_user_routes(email, user_data)

    create_or_update_stagecraft_service(context, TEST_STAGECRAFT_PORT, routes)


def ensure_user_exists(context, email):
    user_data = {
        "email": email,
        "data_sets": [],
    }

    routes = _get_user_routes(email, user_data)

    create_or_update_stagecraft_service(context, TEST_STAGECRAFT_PORT, routes)

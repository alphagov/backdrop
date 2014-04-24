

def ensure_user_has_permissions(context, email, data_sets):
    user_data = {
        "_id": email,
        "email": email,
        "data_sets": data_sets
    }
    context.client.storage()["users"].save(user_data)


def ensure_user_exists(context, email):
    user_data = {
        "_id": email,
        "email": email,
        "data_sets": [],
    }
    context.client.storage()["users"].save(user_data)

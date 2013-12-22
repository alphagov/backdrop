

def ensure_user_has_permissions(context, email, buckets):
    user_data = {
        "_id": email,
        "email": email,
        "buckets": buckets
    }
    context.client.storage()["users"].save(user_data)


def ensure_user_exists(context, email):
    user_data = {
        "_id": email,
        "email": email,
        "buckets": [],
    }
    context.client.storage()["users"].save(user_data)

from behave import *


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


@given(u'I am logged in')
def step(context):
    context.execute_steps(u'given I am logged in as "testuser" with email "test@example.com"')


@given(u'I am logged in as "{name}" with email "{email}"')
def step(context, name, email):
    testuser = (name, email)
    ensure_user_exists(context, email)
    context.user_email = email
    context.client.get("/_user/sign_in/test?user=%s&email=%s" % testuser)


@given('I can upload to "{bucket}"')
def step(context, bucket):
    ensure_user_has_permissions(context, context.user_email, [bucket])

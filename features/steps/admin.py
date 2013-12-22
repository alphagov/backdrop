from behave import *
from ..support.authentication import \
    ensure_user_has_permissions, ensure_user_exists


@given(u'admin I am logged in as "{name}" with email "{email}"')
def step(context, name, email):
    testuser = (name, email)
    ensure_user_exists(context, email)
    context.user_email = email
    context.client.get("/sign-in/test?user=%s&email=%s" % testuser)

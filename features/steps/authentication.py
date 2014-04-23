from behave import *
from ..support.authentication import \
    ensure_user_has_permissions, ensure_user_exists


@given('I can upload to "{data_set}"')
def step(context, data_set):
    ensure_user_has_permissions(context, context.user_email, [data_set])


@given(u'I am logged in')
def step(context):
    context.execute_steps(u'given I am logged in as "testuser" with email "test@example.com"')


@given(u'I am logged in as "{name}" with email "{email}"')
def step(context, name, email):
    testuser = (name, email)
    ensure_user_exists(context, email)
    context.user_email = email
    context.client.get("/sign-in/test?user=%s&email=%s" % testuser)

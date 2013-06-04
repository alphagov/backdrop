import os
from behave import *
import datetime
from dateutil import parser
from flask import json
from hamcrest import *

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


@given('I have the data in "{fixture_name}"')
def step(context, fixture_name):
    path_to_fixture = os.path.join(FIXTURE_PATH, fixture_name)
    with open(path_to_fixture) as fixture:
        context.data_to_post = fixture.read()


@given(u'I am logged in')
def step(context):
    context.execute_steps(u'given I am logged in as "testuser"')


@given(u'I am logged in as "{name}"')
def step(context, name):
    testuser = (name, "test@example.com")
    context.client.get("/_user/sign_in/test?user=%s&email=%s" % testuser)


@when('I post the data to "{bucket_name}"')
def step(context, bucket_name):
    context.bucket = bucket_name.replace('/', '')
    context.response = context.client.post(
        bucket_name,
        data=context.data_to_post,
        content_type="application/json",
        headers=[('Authorization', "Bearer %s-bearer-token" % context.bucket)],
    )


@when('I post the file "{filename}" to "/{bucket_name}/upload"')
def step(context, filename, bucket_name):
    context.bucket = bucket_name.replace('/', '')
    context.response = context.client.post(
        "/" + bucket_name + "/upload",
        files={"file": open("tmp/%s" % filename, "r")},
        headers=[('Authorization', "Bearer %s-bearer-token" % context.bucket)],
    )


@then('the stored data should contain "{amount}" "{key}" equaling "{value}"')
def step(context, amount, key, value):
    result = context.client.storage()[context.bucket].find({key: value})
    assert_that(list(result), has_length(int(amount)))


@then('the stored data should contain "{amount}" "{key}" on "{time}"')
def step(context, amount, key, time):
    time_query = parser.parse(time)
    result = context.client.storage()[context.bucket].find({key: time_query})
    assert_that(list(result), has_length(int(amount)))

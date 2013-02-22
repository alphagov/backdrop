from behave import *
from flask import json
from hamcrest import *

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


@given("...")
def step(context):
    pass


@given('I have the data in "{fixture_name}"')
def step(context, fixture_name):
    path_to_fixture = os.path.join(FIXTURE_PATH, fixture_name)
    with open(path_to_fixture) as fixture:
        context.data_to_post = fixture.read()


@when('I post the data to "{bucket_name}"')
def step(context, bucket_name):
    context.bucket = bucket_name.replace('/', '')
    context.response = context.api.post(
        bucket_name,
        data=context.data_to_post,
        content_type="application/json"
    )


@then('the stored data should contain "{amount}" "{key}" equaling "{value}"')
def step(context, amount, key, value):
    result = context.mongo[context.bucket].find({key: value})
    assert_that(list(result), has_length(int(amount)))

import os
import re
import test_helper
from behave import *
from flask import json
from hamcrest import *
from dateutil import parser
import pytz

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


@given('"{fixture_name}" is in "{bucket_name}" bucket')
def step(context, fixture_name, bucket_name):
    fixture_path = os.path.join(FIXTURE_PATH, fixture_name)
    with open(fixture_path) as fixture:
        for obj in json.load(fixture):
            if '_timestamp' in obj:
                obj['_timestamp'] = parser.parse(obj['_timestamp'])\
                    .astimezone(pytz.utc)
            context.mongo[bucket_name].save(obj)
    context.bucket = bucket_name


@when('I go to "{query}"')
def step(context, query):
    context.response = context.api.get(query)


@then('I should get back a status of "{expected_status}"')
def step(context, expected_status):
    assert_that(context.response.status_code, is_(int(expected_status)))


@then('the JSON should have "{n}" result(s)')
def step(context, n):
    the_data = json.loads(context.response.data)['data']
    assert_that(the_data, has_length(int(n)))


@then('the "{nth}" result should be "{expected_json}"')
def step(context, nth, expected_json):
    i = int(re.compile(r'\d+').match(nth).group(0)) - 1
    the_data = json.loads(context.response.data)['data']
    expected = json.loads(expected_json)
    assert_that(the_data[i], is_(expected))

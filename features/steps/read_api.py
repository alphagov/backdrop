import os
import re
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
            if '_week_start_at' in obj:
                obj['_week_start_at'] = parser.parse(obj['_week_start_at']) \
                    .astimezone(pytz.utc)
            context.client.storage()[bucket_name].save(obj)
    context.bucket = bucket_name


@when('I go to "{query}"')
def step(context, query):
    context.response = context.client.get(query)


@then('I should get back a status of "{expected_status}"')
def step(context, expected_status):
    assert_that(context.response.status_code, is_(int(expected_status)))


@then('I should get back a message: "{expected_message}"')
def step(context, expected_message):
    assert_that(
        json.loads(context.response.data),
        is_(json.loads(expected_message)))


step_matcher("re")


@then('the JSON should have "(?P<n>\d+)" results?')
def step(context, n):
    the_data = json.loads(context.response.data)['data']
    assert_that(the_data, has_length(int(n)))


step_matcher("parse")


@then('the "{nth}" result should be "{expected_json}"')
def step(context, nth, expected_json):
    i = int(re.compile(r'\d+').match(nth).group(0)) - 1
    the_data = json.loads(context.response.data)['data']
    expected = json.loads(expected_json)
    assert_that(the_data[i], is_(expected))


@then('the "{nth}" result should have "{key}" equaling "{value}"')
def step(context, nth, key, value):
    i = int(re.compile(r'\d+').match(nth).group(0)) - 1
    the_data = json.loads(context.response.data)['data']
    assert_that(the_data[i][key], is_(value))

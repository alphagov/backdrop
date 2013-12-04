import os
import re
from behave import *
from flask import json
from hamcrest import *
from dateutil import parser
import datetime
import re
import pytz

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


@given('the api is running in protected mode')
def step(context):
    context.client.set_config_parameter('PREVENT_RAW_QUERIES', True)


def ensure_bucket_exists(context, bucket_name):
    context.bucket = bucket_name
    bucket_data = {
        '_id': bucket_name,
        'name': bucket_name,
        'data_group': bucket_name,
        'data_type': bucket_name,
        'bearer_token': "%s-bearer-token" % bucket_name
    }
    context.client.storage()["buckets"].save(bucket_data)


@given('"{fixture_name}" is in "{bucket_name}" bucket')
def step(context, fixture_name, bucket_name):
    ensure_bucket_exists(context, bucket_name)
    fixture_path = os.path.join(FIXTURE_PATH, fixture_name)
    with open(fixture_path) as fixture:
        for obj in json.load(fixture):
            for key in ['_timestamp', '_week_start_at', '_month_start_at']:
                if key in obj:
                    obj[key] = parser.parse(obj[key]).astimezone(pytz.utc)
            context.client.storage()[bucket_name].save(obj)


@given('I have a record updated "{timespan}" ago in the "{bucket_name}" bucket')
def step(context, timespan, bucket_name):
    ensure_bucket_exists(context, bucket_name)
    now = datetime.datetime.now()
    number_of_seconds = int(re.match(r'^(\d+) seconds?', timespan).group(1))
    timedelta = datetime.timedelta(seconds=number_of_seconds)
    updated = now - timedelta
    record = {
        "_updated_at": updated
    }
    context.client.storage()[bucket_name].save(record)


@given('I have a bucket named "{bucket_name}"')
def step(context, bucket_name):
    ensure_bucket_exists(context, bucket_name)


@given('bucket setting {setting} is {set_to}')
def step(context, setting, set_to):
    if set_to == "None":
        set_to = None
    else:
        set_to = json.loads(set_to)
    context.client.storage()["buckets"].update(
        {"_id": context.bucket}, {"$set": {setting: set_to}}, safe=True)


@when('I go to "{query}"')
def step(context, query):
    context.response = context.client.get(query)


@when('I send another request to "{query}" with the received etag')
def step(context, query):
    etag = context.response.headers["ETag"]
    context.response = context.client.get(query,
                                          headers={"If-None-Match": etag})


@then('I should get back a status of "{expected_status}"')
def step(context, expected_status):
    assert_that(context.response.status_code, is_(int(expected_status)))


@then('I should get a "{header}" header of "{value}"')
def step(context, header, value):
    assert_that(context.response.headers.get(header), is_(value))


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


def parse_position(nth, data):
    match = re.compile(r'\d+').match(nth)
    if match:
        return int(match.group(0)) - 1
    elif nth == "last":
        return len(data) - 1
    elif nth == "first":
        return 0
    else:
        raise IndexError(nth)


@then('the "{nth}" result should be "{expected_json}"')
def step(context, nth, expected_json):
    the_data = json.loads(context.response.data)['data']
    i = parse_position(nth, the_data)
    expected = json.loads(expected_json)
    assert_that(the_data[i], is_(expected))


@then('the "{nth}" result should have "{key}" equaling "{value}"')
def step(context, nth, key, value):
    the_data = json.loads(context.response.data)['data']
    i = parse_position(nth, the_data)
    assert_that(the_data[i][key], equal_to(value))


@then('the "{nth}" result should have "{key}" equaling the integer "{value}"')
def step(context, nth, key, value):
    the_data = json.loads(context.response.data)['data']
    i = parse_position(nth, the_data)
    assert_that(the_data[i][key], equal_to(int(value)))


@then('the "{nth}" result should have "{key}" with item "{value}"')
def step(context, nth, key, value):
    the_data = json.loads(context.response.data)['data']
    i = parse_position(nth, the_data)
    assert_that(the_data[i][key], has_item(json.loads(value)))


@then('the "{nth}" result should have "{key}" with item with entries "{value}"')
def step(context, nth, key, value):
    the_data = json.loads(context.response.data)['data']
    i = parse_position(nth, the_data)
    assert_that(the_data[i][key], has_item(has_entries(json.loads(value))))


@then('the "{nth}" result should have "{key}" with json "{expected_json}"')
def impl(context, nth, key, expected_json):
    the_data = json.loads(context.response.data)['data']
    i = parse_position(nth, the_data)
    assert_that(the_data[i][key], is_(json.loads(expected_json)))


@then('the "{nth}" result should have a sub group with "{key}" with json "{expected_json}"')
def impl(context, nth, key, expected_json):
    the_data = json.loads(context.response.data)['data']
    i = parse_position(nth, the_data)
    assert_that(the_data[i]['values'],
                has_item(
                    has_entry(key, json.loads(expected_json))))


@then('the "{header}" header should be "{value}"')
def step(context, header, value):
    assert_that(context.response.headers.get(header), is_(value))


@then(u'the error message should be "{expected_message}"')
def impl(context, expected_message):
    error_message = json.loads(context.response.data)['message']
    assert_that(error_message, is_(expected_message))

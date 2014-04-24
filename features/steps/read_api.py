import os
import re
from behave import *
from flask import json
from hamcrest import *
from dateutil import parser
import datetime
import re
import pytz
from features.support.stagecraft import StagecraftService

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), '..', 'fixtures')
TEST_STAGECRAFT_PORT = 3204


@given('the api is running in protected mode')
def step(context):
    context.client.set_config_parameter('PREVENT_RAW_QUERIES', True)


def ensure_data_set_exists(context, data_set_name, settings={}):
    # these should mostly match the default DataSetConfig.__new__() kwargs
    response = {
        'name': data_set_name,
        'data_group': data_set_name,
        'data_type': data_set_name,
        'raw_queries_allowed': False,
        'bearer_token': '%s-bearer-token' % data_set_name,
        'upload_format': 'csv',
        'upload_filters': ['backdrop.core.upload.filters.first_sheet_filter'],
        'auto_ids': None,
        'queryable': True,
        'realtime': False,
        'capped_size': 5040,
        'max_age_expected': 2678400,
    }

    response.update(settings)

    url_response_dict = {
        ('GET', u'data-sets/{}'.format(data_set_name)): response,
        ('GET', u'data-sets'): [response],
        ('GET', u'data-sets?data-group={}&data-type={}'.format(
            response['data_group'], response['data_type'])): [response],
    }

    if 'mock_stagecraft_server' in context and context.mock_stagecraft_server:
        context.mock_stagecraft_server.stop()
    context.mock_stagecraft_server = StagecraftService(
        TEST_STAGECRAFT_PORT, url_response_dict)
    context.mock_stagecraft_server.start()

    context.data_set = data_set_name
    data_set_data = {
        '_id': data_set_name,
        'name': data_set_name,
        'data_group': data_set_name,
        'data_type': data_set_name,
        'bearer_token': "%s-bearer-token" % data_set_name
    }
    context.client.storage()["data_sets"].save(data_set_data)


@given('"{fixture_name}" is in "{data_set_name}" data_set')
def step(context, fixture_name, data_set_name):
    ensure_data_set_exists(context, data_set_name)
    fixture_path = os.path.join(FIXTURE_PATH, fixture_name)
    with open(fixture_path) as fixture:
        for obj in json.load(fixture):
            for key in ['_timestamp', '_day_start_at', '_week_start_at', '_month_start_at']:
                if key in obj:
                    obj[key] = parser.parse(obj[key]).astimezone(pytz.utc)
            context.client.storage()[data_set_name].save(obj)


def get_data_set_settings_from_context_table(table):
    def to_py(string_in):
        if string_in == "None":
            return None
        else:
            return json.loads(string_in)
    return {row['key']: to_py(row['value']) for row in table}


@given('"{fixture_name}" is in "{data_set_name}" data_set with settings')
def step(context, fixture_name, data_set_name):
    settings = get_data_set_settings_from_context_table(context.table)

    ensure_data_set_exists(context, data_set_name, settings)
    fixture_path = os.path.join(FIXTURE_PATH, fixture_name)
    with open(fixture_path) as fixture:
        for obj in json.load(fixture):
            for key in ['_timestamp', '_day_start_at', '_week_start_at', '_month_start_at']:
                if key in obj:
                    obj[key] = parser.parse(obj[key]).astimezone(pytz.utc)
            context.client.storage()[data_set_name].save(obj)


@given('I have a record updated "{timespan}" ago in the "{data_set_name}" data_set')
def step(context, timespan, data_set_name):
    now = datetime.datetime.now()
    number_of_seconds = int(re.match(r'^(\d+) seconds?', timespan).group(1))
    timedelta = datetime.timedelta(seconds=number_of_seconds)
    updated = now - timedelta
    record = {
        "_updated_at": updated
    }
    context.client.storage()[data_set_name].save(record)


@given('I have a data_set named "{data_set_name}" with settings')
def step(context, data_set_name):
    settings = get_data_set_settings_from_context_table(context.table)
    ensure_data_set_exists(context, data_set_name, settings)


@given('I have a data_set named "{data_set_name}"')
def step(context, data_set_name):
    ensure_data_set_exists(context, data_set_name)


@given('Stagecraft is running')
def step(context):
    if 'mock_stagecraft_server' in context and context.mock_stagecraft_server:
        context.mock_stagecraft_server.stop()
    context.mock_stagecraft_server = StagecraftService(
        TEST_STAGECRAFT_PORT, {})
    context.mock_stagecraft_server.start()


@when('I go to "{query}"')
def step(context, query):
    context.response = context.client.get(query)


@when('I send another request to "{query}" with the received etag')
def step(context, query):
    etag = context.response.headers["ETag"]
    context.response = context.client.get(query,
                                          headers={"If-None-Match": etag})


def get_error_message(response_data):
    message = ""
    try:
        message = json.loads(response_data).get('message', "")
    except:
        pass
    return message


@then('I should get back a status of "{expected_status}"')
def step(context, expected_status):
    assert_that(context.response.status_code, is_(int(expected_status)),
                get_error_message(context.response.data))


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
    response_data = json.loads(context.response.data)
    assert_that('data' in response_data, response_data.get('message', None))
    the_data = response_data['data']
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

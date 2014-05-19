import os

from behave import given, when, then
from dateutil import parser
from hamcrest import assert_that, has_length, equal_to


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


@given('I have the data in "{fixture_name}"')
def step(context, fixture_name):
    path_to_fixture = os.path.join(FIXTURE_PATH, fixture_name)
    with open(path_to_fixture) as fixture:
        context.data_to_post = fixture.read()


@given("I have JSON data '{json}'")
def step(context, json):
    context.data_to_post = json


@given("I have an empty request body")
def step(context):
    context.data_to_post = ''


@given('I use the bearer token for the data_set')
def step(context):
    context.bearer_token = "%s-bearer-token" % context.data_set


@given(u'I have the bearer token "{token}"')
def step(context, token):
    context.bearer_token = token


@when('I {http_method} to the specific path "{path}"')
def step(context, http_method, path):
    assert http_method in ('POST', 'PUT'), "Only support POST, PUT"
    http_function = {
        'POST': context.client.post,
        'PUT': context.client.put
    }[http_method]

    context.response = http_function(
        path,
        data=context.data_to_post,
        content_type="application/json",
        headers=_make_headers_from_context(context),
    )


@when('I {http_method} to "{path}" with a malformed authorization header')
def step(context, http_method, path):
    assert http_method in ('POST', 'PUT'), "Only support POST, PUT"
    http_function = {
        'POST': context.client.post,
        'PUT': context.client.put
    }[http_method]

    context.response = http_function(
        path,
        data=context.data_to_post,
        content_type="application/json",
        headers=_make_malformed_header_from_context(context),
    )


@when('I POST the file "{filename}" to "/{data_set_name}/upload"')
def step(context, filename, data_set_name):
    context.data_set = data_set_name.replace('/', '')
    context.response = context.client.post(
        "/" + data_set_name + "/upload",
        files={"file": open("tmp/%s" % filename, "r")},
        headers=_make_headers_from_context(context),
    )


@when('I send a DELETE request to "{data_set_url}"')
def step(context, data_set_url):
    context.response = context.client.delete(
        data_set_url,
        headers=_make_headers_from_context(context)
    )


@then('the stored data should contain "{amount}" "{key}" equaling "{value}"')
def step(context, amount, key, value):
    result = context.client.storage()[context.data_set].find({key: value})
    assert_that(list(result), has_length(int(amount)))


@then('the stored data should contain "{amount}" "{key}" on "{time}"')
def step(context, amount, key, time):
    time_query = parser.parse(time)
    result = context.client.storage()[context.data_set].find({key: time_query})
    assert_that(list(result), has_length(int(amount)))


@then(u'the collection called "{collection}" should contain {count} records')
def step(context, collection, count):
    result = context.client.storage()[collection].find({})
    assert_that(list(result), has_length(int(count)))


@then('the collection called "{collection}" should exist')
def step(context, collection):
    assert collection in context.client.storage().collection_names()


@then('the collection called "{collection}" should not exist')
def step(context, collection):
    assert collection not in context.client.storage().collection_names()


@then('the collection called "{collection}" should be uncapped')
def step(context, collection):
    options = context.client.storage()[collection].options()
    assert options['capped'] is False


@then('the collection called "{collection}" should be capped at "{size}"')
def step(context, collection, size):
    options = context.client.storage()[collection].options()
    assert options['capped'] is True

    assert_that(int(options['size']), equal_to(int(size)))


def _make_headers_from_context(context):
    if context and 'bearer_token' in context:
        return [('Authorization', "Bearer %s" % context.bearer_token)]
    return []


def _make_malformed_header_from_context(context):
    if context and 'bearer_token' in context:
        return [('Orthoriszation', "Bearer %s" % context.bearer_token)]
    return []

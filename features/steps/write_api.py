import gzip
import os

from behave import given, when, then
from dateutil import parser
from hamcrest import assert_that, has_length, equal_to
from io import BytesIO

from backdrop.core.query import Query
from backdrop.core.timeseries import DAY, WEEK

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


@given(u'I have compressed content')
def step(context):
    context.content_encoding = True


@when('I "{http_method}" the compressed request body to the path "{path}"')
def step(context, http_method, path):
    assert http_method in ('POST', 'PUT'), "Only support POST, PUT"
    http_function = {
        'POST': context.client.post,
        'PUT': context.client.put
    }[http_method]

    def compress_data(io):
        bio = BytesIO()
        f = gzip.GzipFile(filename='', mode='wb', fileobj=bio)
        f.write(io)
        f.close()
        return bio.getvalue()

    headers = _make_headers_from_context(context)
    headers.append(('Content-Encoding', u'gzip'))

    context.response = http_function(
        path,
        data=compress_data(context.data_to_post),
        content_type="application/json",
        headers=headers,
    )


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
    result = context.client.storage().execute_query(context.data_set, Query.create(filter_by=[(key, value)]))
    assert_that(list(result), has_length(int(amount)))


@then('the stored data should contain "{amount}" "{key}" on "{time}"')
def step(context, amount, key, time):
    time_query = parser.parse(time)
    if key == '_start_at':
        query = Query.create(start_at=time_query, period=DAY, duration=1)
    elif key == '_end_at':
        query = Query.create(end_at=time_query, period=DAY, duration=-1)
    elif key == '_week_start_at':
        query = Query.create(start_at=time_query, period=WEEK, duration=1)
    else:
        raise NotImplementedError(key)
    result = context.client.storage().execute_query(context.data_set, query)
    assert_that(result, has_length(1))
    assert_that(result[0]['_count'], equal_to(int(amount)))


@then(u'the collection called "{collection}" should contain {count} records')
def step(context, collection, count):
    result = context.client.storage().execute_query(collection, Query.create())
    assert_that(list(result), has_length(int(count)))


@then('the collection called "{collection}" should not exist')
def step(context, collection):
    result = context.client.storage().execute_query(collection, Query.create())
    assert_that(result, has_length(0))


def _make_headers_from_context(context):
    result = []
    if context and 'bearer_token' in context:
        result.append(('Authorization', "Bearer %s" % context.bearer_token))
    if context and 'content_encoding' in context:
        result.append(('Content-Encoding', u'gzip'))
    return result


def _make_malformed_header_from_context(context):
    if context and 'bearer_token' in context:
        return [('Orthoriszation', "Bearer %s" % context.bearer_token)]
    return []

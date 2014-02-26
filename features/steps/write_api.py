import os
from behave import given, when, then
from dateutil import parser
from hamcrest import assert_that, has_length, equal_to

from tests.support.bucket import pretend_this_bucket_exists
from backdrop.core.bucket import BucketConfig

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


@given('I have the data in "{fixture_name}"')
def step(context, fixture_name):
    path_to_fixture = os.path.join(FIXTURE_PATH, fixture_name)
    with open(path_to_fixture) as fixture:
        context.data_to_post = fixture.read()


@given("I have JSON data '{json}'")
def step(context, json):
    context.data_to_post = json


@given('I use the bearer token for the bucket')
def step(context):
    context.bearer_token = "%s-bearer-token" % context.bucket


@given(u'I have the bearer token "{token}"')
def step(context, token):
    context.bearer_token = token

@contextmanager
def fake_bucket_if_necessary(context):
    if 'fake_bucket_name' in context:
        with pretend_bucket_exists(
                BucketConfig(context.fake_bucket_name),


@when('I post the data to "{bucket_name}"')
def step(context, bucket_name):

    if not (context and 'bucket' in context):
        # TODO: this is coming out as ie data-setsbucketname - investigate?!
        context.bucket = bucket_name.replace('/', '')

    with fake_bucket_if_necessary(context):
         context.response = context.client.post(
            bucket_name,
            data=context.data_to_post,
            content_type="application/json",
            headers=_make_headers_from_context(context),
        )

   if 'should_fake_bucket' in contet and context.should_fake_bucket:
    token = context.bearer_token if 'bearer_token' in context else None
    with pretend_this_bucket_exists(
            BucketConfig(
                bucket_name.strip('/'),
                'data_group',
                'data_type',
                bearer_token=token
            )):


@when('I post to the specific path "{path}"')
def step(context, path):
    context.response = context.client.post(
        path,
        data=context.data_to_post,
        content_type="application/json",
        headers=_make_headers_from_context(context),
    )


@when('I post the file "{filename}" to "/{bucket_name}/upload"')
def step(context, filename, bucket_name):
    context.bucket = bucket_name.replace('/', '')
    context.response = context.client.post(
        "/" + bucket_name + "/upload",
        files={"file": open("tmp/%s" % filename, "r")},
        headers=_make_headers_from_context(context),
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

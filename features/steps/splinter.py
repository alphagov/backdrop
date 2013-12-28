import json
import os
import shutil
import datetime
from hamcrest import *

from backdrop.core.timeutils import utc


@when(u'I enter "{filename}" into the file upload field')
def step(context, filename):
    filepath = "tmp/%s" % filename
    context.client.browser.attach_file('file', filepath)


@when(u'I click "{element_text}"')
def step(context, element_text):
    context.client.browser.find_by_value(element_text).first.click()


@then(u'I should see the text "{message}"')
def step(context, message):
    assert context.client.browser.is_text_present(message)


@then(u'the "{bucket_name}" bucket should contain in any order')
def step(context, bucket_name):
    bucket_contains(context, bucket_name, contains_inanyorder)


@then(u'the "{bucket_name}" bucket should have items')
def step(context, bucket_name):
    bucket_contains(context, bucket_name, has_items)


def bucket_contains(context, bucket_name, sequence_matcher):
    documents = [json.loads(line) for line in context.text.split("\n")]
    matchers = [has_entries(doc) for doc in documents]

    bucket = context.client.storage()[bucket_name]
    records = [datetimes_to_strings(record) for record in bucket.find()]
    records = [ints_to_floats(record) for record in records]
    records = [nones_to_zeroes(record) for record in records]

    assert_that(records, sequence_matcher(*matchers))


def datetimes_to_strings(record):
    for key, value in record.items():
        if isinstance(value, datetime.datetime):
            record[key] = unicode(utc(value).isoformat())

    return record


def ints_to_floats(record):
    for key, value in record.items():
        if isinstance(value, int):
            record[key] = float(value)

    return record


def nones_to_zeroes(record):
    for key, value in record.items():
        if value is None:
            record[key] = 0.0

    return record


@then(u'the platform should have "{n}" items stored in "{bucket_name}"')
def step(context, n, bucket_name):
    bucket = context.client.storage()[bucket_name]
    assert_that(bucket.count(), is_(int(n)))

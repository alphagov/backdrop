import json
import os
import shutil
import datetime
from hamcrest import *

from backdrop.core.timeutils import utc


@given(u'a file named "{filename}" with fixture "{fixturename}"')
def step(context, filename, fixturename):
    filepath = os.path.join("tmp", filename)
    fixturepath = os.path.join("features", "fixtures", fixturename)
    shutil.copyfile(fixturepath, filepath)


@given(u'a file named "{filename}"')
def step(context, filename):
    content = context.text.encode('utf-8')
    filepath = os.path.join("tmp", filename)
    with open(filepath, "w") as stream:
        stream.write(content)


@given(u'a file named "{filename}" of size "{number}" bytes')
def step(context, filename, number):
    filepath = os.path.join("tmp", filename)
    with open(filepath, "w") as stream:
        stream.write("x" * int(number))


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

    assert_that(records, sequence_matcher(*matchers))


def datetimes_to_strings(record):
    for key, value in record.items():
        if isinstance(value, datetime.datetime):
            record[key] = utc(value).isoformat()

    return record


@then(u'the platform should have "{n}" items stored in "{bucket_name}"')
def step(context, n, bucket_name):
    bucket = context.client.storage()[bucket_name]
    assert_that(bucket.count(), is_(int(n)))

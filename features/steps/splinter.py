import datetime
import json

from behave import when, when
from hamcrest import contains_inanyorder, has_items, has_entries, \
    assert_that, is_

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


@then(u'I should see the signed in user "{name}"')
def step(context, name):
    signed_in_text = context.client.browser.evaluate_script(
        'document.querySelector("p.navbar-text").innerText;')
    assert signed_in_text == "Signed in as {}".format(name)


@then(u'the "{data_set_name}" data_set should contain in any order')
def step(context, data_set_name):
    data_set_contains(context, data_set_name, contains_inanyorder)


@then(u'the "{data_set_name}" data_set should have items')
def step(context, data_set_name):
    data_set_contains(context, data_set_name, has_items)


def data_set_contains(context, data_set_name, sequence_matcher):
    documents = [json.loads(line) for line in context.text.split("\n")]
    matchers = [has_entries(doc) for doc in documents]

    data_set = context.client.mongo()[data_set_name]
    records = [datetimes_to_strings(record) for record in data_set.find()]
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


@then(u'the platform should have "{n}" items stored in "{data_set_name}"')
def step(context, n, data_set_name):
    data_set = context.client.mongo()[data_set_name]
    assert_that(data_set.count(), is_(int(n)))

import json
from hamcrest import assert_that, has_length


@given(u'a file named "{filename}"')
def step(context, filename):
    filepath = "tmp/%s" % filename
    with open(filepath, "w") as stream:
        stream.write(context.text)


@when(u'I enter "{filename}" into the file upload field')
def step(context, filename):
    filepath = "tmp/%s" % filename
    context.client.browser.attach_file('file', filepath)


@when(u'I click "{element_text}"')
def step(context, element_text):
    context.client.browser.find_by_value(element_text).first.click()


@then(u'the platform should have stored in "{bucket_name}"')
def step(context, bucket_name):
    bucket = context.client.storage()[bucket_name]
    for line in context.text.split("\n"):
        query = json.loads(line)
        result = bucket.find(query)
        assert_that(list(result), has_length(1))

import os
import shutil

from behave import given


@given(u'a file named "{filename}" with fixture "{fixturename}"')
def step(context, filename, fixturename):
    filepath = os.path.join("tmp", filename)
    fixturepath = os.path.join("features", "fixtures", fixturename)
    shutil.copyfile(fixturepath, filepath)
    context.after_handlers.append(lambda: os.remove(filepath))


@given(u'a file named "{filename}" of size "{number}" bytes')
def step(context, filename, number):
    filepath = os.path.join("tmp", filename)
    with open(filepath, "w") as stream:
        stream.write("x" * int(number))
    context.after_handlers.append(lambda: os.remove(filepath))


@given(u'a file named "{filename}"')
def step(context, filename):
    content = context.text.encode('utf-8')
    filepath = os.path.join("tmp", filename)
    with open(filepath, "w") as stream:
        stream.write(content)
    context.after_handlers.append(lambda: os.remove(filepath))

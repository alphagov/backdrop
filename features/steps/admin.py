from behave import *
from ..support.authentication import \
    ensure_user_has_permissions, ensure_user_exists


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


# TODO: remove admin prefix
@given(u'admin I am logged in')
def step(context):
    context.execute_steps(u'given admin I am logged in as "testuser" with email "test@example.com"')


# TODO: remove admin prefix
@given(u'admin I am logged in as "{name}" with email "{email}"')
def step(context, name, email):
    testuser = (name, email)
    ensure_user_exists(context, email)
    context.user_email = email
    context.client.get("/sign-in/test?user=%s&email=%s" % testuser)

"""Generate a DataSetConfig seed file for a given environment.
"""
import argparse
import os
from shutil import copyfile
import sys
import requests
from werkzeug.utils import import_string
from functools import partial
import re
import json

NGINX_LINE_PATTERN = re.compile(r"'(?P<key>.*?)'\s+=>\s+(?P<value>.*),?")
NGINX_PATH_PATTERN = re.compile(r"(.*)/api/(.*)")


def nginx_extract_line(line):
    match = NGINX_LINE_PATTERN.search(line)
    if match is None:
        raise Exception("Failed to parse line")
    group = match.groupdict()

    return group['key'], nginx_parse_value(group['value'].strip(","))


def nginx_parse_value(value):
    if value.startswith("$"):
        return True
    else:
        return json.loads(value.replace("'", '"'))


def nginx_extract_data_sets(lines):
    data_set = None
    for line in lines:
        if "{" in line:
            pass
        elif "}" in line:
            if data_set is None:
                raise Exception("No data_set to yield")
            else:
                yield data_set
                data_set = None
        else:
            if data_set is None:
                data_set = dict()
            data_set.update([nginx_extract_line(line)])


def nginx_unroll_path(data_set):
    match = NGINX_PATH_PATTERN.match(data_set['path'])
    data_set['data_group'] = match.group(1)
    data_set['data_type'] = match.group(2)

    return data_set


def slice_by_matches(lines, start, end):
    """Extract a slice of lines by start and end markers"""
    started = False
    for line in lines:
        if not started and start in line:
            started = True
        elif end in line:
            break
        elif started:
            yield line


def load_nginx_config(path):
    with open(path) as f:
        lines = slice_by_matches(f.readlines(), "$backdrop_data_sets", "  ]")
        data_sets = nginx_extract_data_sets(lines)
        data_sets = map(nginx_unroll_path, data_sets)
        return dict(
            (b['name'], b) for b in data_sets
        )


def import_config(app, env):
    return import_string("backdrop.%s.config.%s" % (app, env))


def alphagov_config_path(app, config):
    return "../alphagov-deployment/%s/to_upload/%s" % (app, config)


def local_config_path(app, config):
    return "./backdrop/%s/config/%s" % (app, config)


def move_config_into_place(environment):
    copyfile(
        alphagov_config_path("write.backdrop", "production.py"),
        local_config_path("write", "production.py")
    )
    copyfile(
        alphagov_config_path("write.backdrop", "environment.%s.py" %
                                               environment),
        local_config_path("write", "environment.py")

    )
    copyfile(
        alphagov_config_path("read.backdrop", "production.py"),
        local_config_path("read", "production.py")
    )


def create_test_url(environment, data_set):
    if is_production(environment):
        host = "www.gov.uk"
    else:
        host = "www.preview.alphagov.co.uk"

    return "https://%s/performance/%s/api/%s" % (
        host, data_set['data_group'], data_set['data_type'])


def disable_data_sets(predicate, data_sets):
    def func(data_set):
        if predicate(data_set['name']):
            data_set['queryable'] = False
        return data_set
    return map(func, data_sets)


def disable_data_sets_by_prefix(prefix, data_sets):
    return disable_data_sets(lambda name: name.startswith(prefix), data_sets)


def disable_data_sets_by_match(match, data_sets):
    return disable_data_sets(lambda name: name == match, data_sets)


def test_data_set(environment, data_set):
    url = create_test_url(environment, data_set)
    if "AUTH" in os.environ:
        result = requests.get(url, auth=tuple(os.environ['AUTH'].split(":")))
    else:
        result = requests.get(url)

    if data_set['queryable'] and data_set['raw_queries_allowed']:
        return url, 200, result.status_code
    elif data_set['queryable'] and not data_set['raw_queries_allowed']:
        return url, 400, result.status_code
    else:
        return url, 404, result.status_code


def run_tests(environment, data_sets):
    passed = True
    for data_set in data_sets:
        url, expected, actual = test_data_set(environment, data_set)
        if expected != actual:
            print(url, expected, actual)
            passed = False
    return passed


def is_production(environment):
    return environment in ["staging", "production"]


def is_production_like(environment):
    return environment in ["preview", "staging", "production"]


def load_config(environment):
    if is_production_like(environment):
        app_env = "production"
        move_config_into_place(environment)
    else:
        app_env = "development"

    read_config = import_config("read", app_env)
    write_config = import_config("write", app_env)
    nginx_config = load_nginx_config(
        "../puppet/modules/govuk/manifests/apps/publicapi.pp")

    return read_config, write_config, nginx_config


def extract_users(environment, read_config, write_config, nginx_config):
    return [
        {"email": email, "data_sets": data_sets}
        for email, data_sets in write_config.PERMISSIONS.items()]


def extract_data_set(read_config, write_config, nginx_config, name):
    data_set = {
        "name": name,
        "data_group": nginx_config.get(name)['data_group'],
        "data_type": nginx_config.get(name)['data_type'],
        "raw_queries_allowed": read_config.RAW_QUERIES_ALLOWED.get(name,
                                                                   False),
        "bearer_token": write_config.TOKENS.get(name),
        "upload_format": write_config.DATA_SET_UPLOAD_FORMAT.get(name, "csv"),
        "upload_filters": write_config.DATA_SET_UPLOAD_FILTERS.get(name),
        "auto_ids": write_config.DATA_SET_AUTO_ID_KEYS.get(name),
        "queryable": nginx_config.get(name).get('enabled', True),
        "realtime": nginx_config.get(name).get('realtime', False),
        "capped_size": None
    }
    if data_set['realtime']:
        data_set['capped_size'] = 5040
    return data_set


def extract_data_sets(environment, read_config, write_config, nginx_config):
    data_sets = [
        extract_data_set(read_config, write_config, nginx_config, name)
        for name in nginx_config.keys()
    ]

    if is_production(environment):
        data_sets = disable_data_sets_by_prefix("lpa_", data_sets)
        data_sets = disable_data_sets_by_match("test", data_sets)
        data_sets = disable_data_sets_by_match("hmrc_preview", data_sets)

    if is_production_like(environment) and not run_tests(environment, data_sets):
        sys.exit(1)

    return data_sets


def main(model, environment):
    read_config, write_config, nginx_config = load_config(environment)

    extract_models = {
        "users": extract_users,
        "data_sets": extract_data_sets,
    }[model]

    models = extract_models(environment,
                            read_config, write_config, nginx_config)

    print(json.dumps(models, indent=2, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model",
                        choices=["data_sets", "users"],
                        help="The model to generate a seed file for")
    parser.add_argument("environment",
                        choices=["development", "preview", "production"],
                        help="The environment to generate the seed file for")

    args = parser.parse_args()

    main(args.model, args.environment)

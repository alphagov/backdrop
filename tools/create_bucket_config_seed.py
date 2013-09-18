"""Generate a BucketConfig seed file for a given environment.
"""
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


def nginx_extract_buckets(lines):
    bucket = None
    for line in lines:
        if "{" in line:
            pass
        elif "}" in line:
            if bucket is None:
                raise Exception("No bucket to yield")
            else:
                yield bucket
                bucket = None
        else:
            if bucket is None:
                bucket = dict()
            bucket.update([nginx_extract_line(line)])


def nginx_unroll_path(bucket):
    match = NGINX_PATH_PATTERN.match(bucket['path'])
    bucket['data_group'] = match.group(1)
    bucket['data_type'] = match.group(2)

    return bucket


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
        lines = slice_by_matches(f.readlines(), "$backdrop_buckets", "  ]")
        buckets = nginx_extract_buckets(lines)
        buckets = map(nginx_unroll_path, buckets)
        return dict(
            (b['name'], b) for b in buckets
        )


def import_config(app, env):
    return import_string("backdrop.%s.config.%s" % (app, env))


def config_for(read, write, nginx, name):
    bucket = {
        "name": name,
        "data_group": nginx.get(name)['data_group'],
        "data_type": nginx.get(name)['data_type'],
        "raw_queries_allowed": read.RAW_QUERIES_ALLOWED.get(name, False),
        "bearer_token": write.TOKENS.get(name),
        "upload_format": write.BUCKET_UPLOAD_FORMAT.get(name, "csv"),
        "upload_filters": write.BUCKET_UPLOAD_FILTERS.get(name),
        "auto_ids": write.BUCKET_AUTO_ID_KEYS.get(name),
        "queryable": nginx.get(name).get('enabled', True),
        "realtime": nginx.get(name).get('realtime', False),
        "capped_size": None
    }
    if bucket['realtime']:
        bucket['capped_size'] = 5040
    return bucket


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


def create_test_url(environment, bucket):
    if is_production(environment):
        host = "www.gov.uk"
    else:
        host = "www.preview.alphagov.co.uk"

    return "https://%s/performance/%s/api/%s" % (
        host, bucket['data_group'], bucket['data_type'])


def disable_buckets(predicate, buckets):
    def func(bucket):
        if predicate(bucket['name']):
            bucket['queryable'] = False
        return bucket
    return map(func, buckets)


def disable_buckets_by_prefix(prefix, buckets):
    return disable_buckets(lambda name: name.startswith(prefix), buckets)


def disable_buckets_by_match(match, buckets):
    return disable_buckets(lambda name: name == match, buckets)


def test_bucket(environment, bucket):
    url = create_test_url(environment, bucket)
    if "AUTH" in os.environ:
        result = requests.get(url, auth=tuple(os.environ['AUTH'].split(":")))
    else:
        result = requests.get(url)

    if bucket['queryable'] and bucket['raw_queries_allowed']:
        return url, 200, result.status_code
    elif bucket['queryable'] and not bucket['raw_queries_allowed']:
        return url, 400, result.status_code
    else:
        return url, 404, result.status_code


def run_tests(environment, buckets):
    passed = True
    test_results = map(partial(test_bucket, environment), buckets)
    for name, expected, actual in test_results:
        if expected != actual:
            print(name, expected, actual)
            passed = False
    return passed


def is_production(environment):
    return environment in ["staging", "production"]


def is_production_like(environment):
    return environment in ["preview", "staging", "production"]


def main(environment):
    if is_production_like(environment):
        app_env = "production"
        move_config_into_place(environment)
    else:
        app_env = "development"

    read_config = import_config("read", app_env)
    write_config = import_config("write", app_env)
    nginx_config = load_nginx_config(
        "../puppet/modules/govuk/manifests/apps/publicapi.pp")

    partial_config_for = partial(config_for,
                                 read_config, write_config, nginx_config)

    buckets = map(partial_config_for, nginx_config.keys())

    if is_production(environment):
        buckets = disable_buckets_by_prefix("lpa_", buckets)
        buckets = disable_buckets_by_match("test", buckets)
        buckets = disable_buckets_by_match("hmrc_preview", buckets)

    if is_production_like(environment) and not run_tests(environment, buckets):
        sys.exit(1)

    print(json.dumps(buckets, indent=2, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Must provide a target environment")
        sys.exit(1)
    main(*sys.argv[1:])

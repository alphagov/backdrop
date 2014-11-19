#!/usr/bin/env python
# encoding: utf-8
from performanceplatform import client
from flask import Flask
from os import getenv
import requests
import json
import datetime
import re
from sets import Set
import base64
import pymongo

GOVUK_ENV = getenv("GOVUK_ENV", "development")
app = Flask("backdrop.read.api", static_url_path="/static")
app.config.from_object(
    "backdrop.read.config.{}".format(GOVUK_ENV))

from backdrop.core.storage.mongo import MongoStorageEngine
storage = MongoStorageEngine.create(
    app.config['MONGO_HOSTS'],
    app.config['MONGO_PORT'],
    app.config['DATABASE_NAME'])

admin_api = client.AdminAPI(
    app.config['STAGECRAFT_URL'],
    app.config['SIGNON_API_USER_TOKEN'],
    dry_run=False,
)


def had_default_id(config):
    has = False
    data = [i for i in storage._db[config['name']]
            .find({
                '_updated_at': {
                    '$lt': datetime.datetime(2014, 11, 13, 0, 0),
                    '$gte': datetime.datetime(2014, 11, 01, 0, 0)}
            })]
    if len(data) == 0:
        return True
    for data_point in data:
        if 'humanId' in data_point and 'timeSpan' in data_point:
            if('week' in data_point['humanId']
               or 'day' in data_point['humanId']):
                has = True
                break
    return has


def generate_id(data_point):
    def value_id(value):
        value_bytes = value.encode('utf-8')
        return base64.urlsafe_b64encode(value_bytes), value

    existing_human_id = data_point['humanId']
    regex = re.compile('\d{14}')
    date_part = regex.findall(data_point['humanId'])[0]
    parts = regex.split(data_point['humanId'])
    first_part = parts.pop(0)
    first_part = first_part + date_part
    parts.insert(0, first_part)
    parts.insert(1, "_{}".format(data_point['timeSpan']))
    string_for_id = "".join(parts)
    return value_id(string_for_id)


groups_and_types = [
    {'data_group': u'accelerated-possession-eviction', 'data_type': u'journey'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'browser-usage'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'completion-by-goal'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'conversions-by-keyword'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'conversions-by-landing-page'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'conversions-by-medium'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'conversions-by-social-network'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'conversions-by-source'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'device-usage'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'new-returning-count'},
    {'data_group': u'carers-allowance', 'data_type': u'journey'},
    {'data_group': u'carers-allowance', 'data_type': u'organic-rate'},
    {'data_group': u'carers-allowance', 'data_type': u'referrers-rate'},
    {'data_group': u'carers-allowance', 'data_type': u'social-rate'},
    {'data_group': u'carers-allowance', 'data_type': u'time-taken-to-complete'},
    {'data_group': u'digital-marketplace', 'data_type': u'browsers'},
    {'data_group': u'digital-marketplace', 'data_type': u'devices'},
    {'data_group': u'digital-marketplace', 'data_type': u'traffic-count'},
    {'data_group': u'driving-test-practical-public', 'data_type': u'device-usage'},
    {'data_group': u'driving-test-practical-public', 'data_type': u'journey-help'},
    {'data_group': u'driving-test-practical-public', 'data_type': u'journey'},
    {'data_group': u'employment-tribunal-applications', 'data_type': u'browser-usage'},
    {'data_group': u'employment-tribunal-applications', 'data_type': u'device-usage'},
    {'data_group': u'employment-tribunal-applications', 'data_type': u'new-returning-count'},
    {'data_group': u'govuk', 'data_type': u'browsers'},
    {'data_group': u'govuk', 'data_type': u'devices'},
    {'data_group': u'govuk', 'data_type': u'visitors'},
    {'data_group': u'govuk-info', 'data_type': u'page-statistics'},
    {'data_group': u'govuk-info', 'data_type': u'search-terms'},
    {'data_group': u'insidegov', 'data_type': u'visitors'},
    {'data_group': u'lasting-power-of-attorney', 'data_type': u'journey'},
    {'data_group': u'legal-aid-civil-claims', 'data_type': u'browser-usage'},
    {'data_group': u'legal-aid-civil-claims', 'data_type': u'device-usage'},
    {'data_group': u'licensing', 'data_type': u'browsers'},
    {'data_group': u'licensing', 'data_type': u'devices'},
    {'data_group': u'licensing', 'data_type': u'journey'},
    {'data_group': u'pay-foreign-marriage-certificates', 'data_type': u'journey'},
    {'data_group': u'pay-legalisation-drop-off', 'data_type': u'journey'},
    {'data_group': u'pay-legalisation-post', 'data_type': u'journey'},
    {'data_group': u'pay-register-birth-abroad', 'data_type': u'journey'},
    {'data_group': u'pay-register-death-abroad', 'data_type': u'journey'},
    {'data_group': u'paye-employee-company-car', 'data_type': u'browser-usage'},
    {'data_group': u'paye-employee-company-car', 'data_type': u'device-usage'},
    {'data_group': u'paye-employee-company-car', 'data_type': u'new-returning-count'},
    {'data_group': u'performance-platform', 'data_type': u'browsers'},
    {'data_group': u'performance-platform', 'data_type': u'devices'},
    {'data_group': u'performance-platform', 'data_type': u'traffic-count'},
    {'data_group': u'police-uk-postcode-search', 'data_type': u'browser-usage'},
    {'data_group': u'police-uk-postcode-search', 'data_type': u'device-usage'},
    {'data_group': u'police-uk-postcode-search', 'data_type': u'new-returning-count'},
    {'data_group': u'prison-visits', 'data_type': u'device-usage'},
    {'data_group': u'prison-visits', 'data_type': u'journey'},
    {'data_group': u'renewtaxcredits', 'data_type': u'device-usage'},
    {'data_group': u'renewtaxcredits', 'data_type': u'journey'},
    {'data_group': u'service-submission-portal', 'data_type': u'browsers'},
    {'data_group': u'service-submission-portal', 'data_type': u'devices'},
    {'data_group': u'service-submission-portal', 'data_type': u'traffic-count'},
    {'data_group': u'student-finance', 'data_type': u'browser-usage'},
    {'data_group': u'student-finance', 'data_type': u'device-usage'},
    {'data_group': u'student-finance', 'data_type': u'journey'},
    {'data_group': u'student-finance', 'data_type': u'new-returning-users'},
    {'data_group': u'student-finance', 'data_type': u'site-traffic'},
    {'data_group': u'tier-2-visit-visa', 'data_type': u'devices'},
    {'data_group': u'tier-2-visit-visa', 'data_type': u'journey'},
    {'data_group': u'tier-2-visit-visa', 'data_type': u'volumetrics'},
    {'data_group': u'view-driving-record', 'data_type': u'devices'},
    {'data_group': u'view-driving-record', 'data_type': u'digital-transactions'},
]

if __name__ == '__main__':
    count = 0
    other_timespan = 0
    no_timespan = 0
    no_humanid = 0
    what = 0
    waaaa = 0
    waaaa_stuff = []
    this_stuff = []
    stuff = []
    rar = []
    rar2 = []
    rar3 = []
    other_timespan_stuff = Set([])
    for group_and_type in groups_and_types:
        data_set_config = admin_api.get_data_set(
            group_and_type['data_group'],
            group_and_type['data_type'])

        def current_mongo_collection():
            return storage._db[data_set_config['name']]

        data = [i for i in current_mongo_collection()
                .find({
                    '_updated_at': {
                        '$gte': datetime.datetime(2014, 11, 13, 0, 0)}
                })]

        this_count = 0
        this_other_timespan = 0
        this_other_timespan_stuff = Set([])
        if GOVUK_ENV is 'production':
            env = ''
        else:
            env = GOVUK_ENV + '.'
        url = 'http://www.{}performance.service.gov.uk/data/{}/{}{}'.format(
            env,
            group_and_type['data_group'],
            group_and_type['data_type'],
            "?start_at=2014-10-25T00%3A00%3A00Z&"
            "end_at=2014-11-21T23%3A59%3A59Z"
        )
        if had_default_id(data_set_config):
            for data_point in data:  # ['data']:
                if 'humanId' in data_point and 'timeSpan' in data_point:
                    if('week' not in data_point['humanId']
                       and 'day' not in data_point['humanId']):
                        (the_id, humanId) = generate_id(data_point)
                        if "_{}".format(
                                data_point['timeSpan']) not in humanId:
                            rar.append(humanId)
                        removal = True
                        try:
                            current_mongo_collection().remove(
                                {'_id': data_point['_id']})
                        except pymongo.errors.OperationFailure:
                            rar3.append(data_set_config['name'])
                            removal = False
                        if removal:
                            new_data = data_point
                            new_data['_id'] = the_id
                            new_data['humanId'] = humanId
                            print url
                            try:
                                current_mongo_collection().insert(new_data)
                            except pymongo.errors.DuplicateKeyError:
                                rar2.append(url)
                        count += 1
                        this_count += 1
                    else:
                        other_timespan += 1
                        this_other_timespan += 1
                        this_other_timespan_stuff.add(data_point['timeSpan'])
                        other_timespan_stuff.add(data_point['timeSpan'])
                else:
                    if 'humanId' not in data_point:
                        no_humanid += 1
                    elif 'timeSpan' in data_point:
                        no_timespan += 1
                    else:
                        what += 1
        else:
            stuff.append(url)
        this_stuff.append({url: this_count})
        if this_other_timespan == 0 and not len(data) == 0:
            waaaa_stuff.append(url)
            waaaa += 1
        data = None
    print [
        count,
        other_timespan,
        no_timespan,
        no_humanid,
        what,
        waaaa]
    print other_timespan_stuff
    print "=================="
    print("recollect these manually - these are all collected since"
          "only 3 ruling out search terms")
    print waaaa_stuff
    print json.dumps(this_stuff, indent=2)
    print stuff
    print rar
    print len(rar)
    print rar2
    print len(rar2)
    print rar3
    print len(rar3)

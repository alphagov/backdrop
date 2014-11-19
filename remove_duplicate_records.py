#!/usr/bin/env python
# encoding: utf-8
from performanceplatform import client
from flask import Flask
from os import getenv
import requests
import json
import datetime
from sets import Set

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
    {'data_group': u'blood-donor-appointments', 'data_type': u'journey-by-goal'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'journey-by-goal'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'journey-by-goal'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'journey-by-goal'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'journey-by-goal'},
    {'data_group': u'blood-donor-appointments', 'data_type': u'journey-by-goal'},
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
    {'data_group': u'employment-tribunal-applications', 'data_type': u'journey-by-page'},
    {'data_group': u'employment-tribunal-applications', 'data_type': u'journey-by-page'},
    {'data_group': u'employment-tribunal-applications', 'data_type': u'journey-by-page'},
    {'data_group': u'employment-tribunal-applications', 'data_type': u'new-returning-count'},
    {'data_group': u'govuk', 'data_type': u'browsers'},
    {'data_group': u'govuk', 'data_type': u'devices'},
    {'data_group': u'govuk', 'data_type': u'most_viewed'},
    {'data_group': u'govuk', 'data_type': u'most_viewed_news'},
    {'data_group': u'govuk', 'data_type': u'most_viewed_policies'},
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
    {'data_group': u'view-driving-record', 'data_type': u'digital-transactions'}
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
    other_timespan_stuff = Set([])
    for group_and_type in groups_and_types:
        data_set_config = admin_api.get_data_set(
            group_and_type['data_group'],
            group_and_type['data_type'])
        #get for updated at after 14
        #check getting same data? - yes - both 51481, 12441
        #test remove
        data = [i for i in storage._db[data_set_config['name']]
                .find({
                    '_updated_at': {
                        '$gte': datetime.datetime(2014, 11, 13, 0, 0)}
                })]

        import pdb; pdb.set_trace()

        this_count = 0
        this_other_timespan = 0
        this_no_timespan = 0
        this_no_humanid = 0
        this_what = 0
        this_other_timespan_stuff = Set([])
        if GOVUK_ENV is 'production':
            env = ''
        else:
            env = GOVUK_ENV + '.'
        #env = ''
        print 'requesting {}'.format(group_and_type)
        url = 'http://www.{}performance.service.gov.uk/data/{}/{}{}'.format(
            env,
            group_and_type['data_group'],
            group_and_type['data_type'],
            "?start_at=2014-10-25T00%3A00%3A00Z&"
            "end_at=2014-11-21T23%3A59%3A59Z"
        )
        print url
        #resp = requests.get(url)
        print 'got'
        #data = resp.json()
        for data_point in data:  # ['data']:
            #import pdb; pdb.set_trace()
            if 'humanId' in data_point and 'timeSpan' in data_point:
                if 'week' not in data_point['humanId'] and 'day' not in data_point['humanId']:
                    count += 1
                    this_count += 1
                    print "count"
                    print count
                    print "^count"
                else:
                    other_timespan += 1
                    this_other_timespan += 1
                    print "other timespan"
                    this_other_timespan_stuff.add(data_point['timeSpan'])
                    other_timespan_stuff.add(data_point['timeSpan'])
                    print other_timespan
                    print "^other timespan"
            else:
                if 'humanId' not in data_point:
                    no_humanid += 1
                    print "no_humanid"
                    print no_humanid
                    print "^no_humanid"
                elif 'timeSpan' in data_point:
                    no_timespan += 1
                    print "no_timespan"
                    print no_timespan
                    print "^no_timespan"
                else:
                    what += 1
                    print "what?"
                    print what
                    print "^what?"
        print this_count
        print this_other_timespan
        print this_other_timespan_stuff
        this_stuff.append({url: this_count})
        if this_other_timespan == 0 and not len(data) == 0:
            print "WAAAAAA"
            waaaa_stuff.append(url)
            waaaa += 1
        print "next"
        data = None
        #data_set = client.DataSet.from_group_and_type(
            #app.config['STAGECRAFT_URL'],
            #group_and_type['data_group'],
            #group_and_type['data_type']
        #)
    print [
        count,
        other_timespan,
        no_timespan,
        no_humanid,
        what,
        waaaa]
    print other_timespan_stuff
    print "=================="
    # recollect these manually - these are all collected since
    # only 3 ruling out search terms
    print waaaa_stuff
    print json.dumps(this_stuff, indent=2)
    # purge and push too big - need to remove single record and re push
    #[45808, 6554, 0, 0, 0, 3]
    #====
    #[54835, 6521, 0, 0, 0, 3]

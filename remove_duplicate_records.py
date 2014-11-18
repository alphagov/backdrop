#!/usr/bin/env python
# encoding: utf-8
from performanceplatform import client
from flask import Flask
from os import getenv
import requests
import json
from sets import Set

GOVUK_ENV = getenv("GOVUK_ENV", "development")
app = Flask("backdrop.read.api", static_url_path="/static")
app.config.from_object(
    "backdrop.read.config.{}".format(GOVUK_ENV))

groups_and_types = [
    {'data_group': 'accelerated-possession-eviction', 'data_type': 'journey'},
    {'data_group': 'accelerated-possession-eviction', 'data_type': 'journey'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'browser-usage'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'completion-by-goal'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'conversions-by-keyword'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'conversions-by-landing-page'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'conversions-by-medium'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'conversions-by-social-network'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'conversions-by-source'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'device-usage'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'journey-by-goal'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'journey-by-goal'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'journey-by-goal'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'journey-by-goal'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'journey-by-goal'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'journey-by-goal'},
    {'data_group': 'blood-donor-appointments', 'data_type': 'new-returning-count'},
    {'data_group': 'carers-allowance', 'data_type': 'journey'},
    {'data_group': 'carers-allowance', 'data_type': 'organic-rate'},
    {'data_group': 'carers-allowance', 'data_type': 'referrers-rate'},
    {'data_group': 'carers-allowance', 'data_type': 'social-rate'},
    {'data_group': 'carers-allowance', 'data_type': 'time-taken-to-complete'},
    {'data_group': 'digital-marketplace', 'data_type': 'browsers'},
    {'data_group': 'digital-marketplace', 'data_type': 'devices'},
    {'data_group': 'digital-marketplace', 'data_type': 'traffic-count'},
    {'data_group': 'driving-test-practical-public', 'data_type': 'device-usage'},
    {'data_group': 'driving-test-practical-public', 'data_type': 'journey-help'},
    {'data_group': 'driving-test-practical-public', 'data_type': 'journey'},
    {'data_group': 'employment-tribunal-applications', 'data_type': 'browser-usage'},
    {'data_group': 'employment-tribunal-applications', 'data_type': 'device-usage'},
    {'data_group': 'employment-tribunal-applications', 'data_type': 'journey-by-page'},
    {'data_group': 'employment-tribunal-applications', 'data_type': 'journey-by-page'},
    {'data_group': 'employment-tribunal-applications', 'data_type': 'journey-by-page'},
    {'data_group': 'employment-tribunal-applications', 'data_type': 'new-returning-count'},
    {'data_group': 'govuk', 'data_type': 'browsers'},
    {'data_group': 'govuk', 'data_type': 'devices'},
    {'data_group': 'govuk', 'data_type': 'most_viewed'},
    {'data_group': 'govuk', 'data_type': 'most_viewed_news'},
    {'data_group': 'govuk', 'data_type': 'most_viewed_policies'},
    {'data_group': 'govuk', 'data_type': 'visitors'},
    {'data_group': 'govuk-info', 'data_type': 'page-statistics'},
    #{'data_group': 'govuk-info', 'data_type': 'search-terms'},
    {'data_group': 'insidegov', 'data_type': 'visitors'},
    {'data_group': 'lasting-power-of-attorney', 'data_type': 'journey'},
    {'data_group': 'legal-aid-civil-claims', 'data_type': 'browser-usage'},
    {'data_group': 'legal-aid-civil-claims', 'data_type': 'device-usage'},
    {'data_group': 'licensing', 'data_type': 'browsers'},
    {'data_group': 'licensing', 'data_type': 'devices'},
    {'data_group': 'licensing', 'data_type': 'journey'},
    {'data_group': 'pay-foreign-marriage-certificates', 'data_type': 'journey'},
    {'data_group': 'pay-legalisation-drop-off', 'data_type': 'journey'},
    {'data_group': 'pay-legalisation-post', 'data_type': 'journey'},
    {'data_group': 'pay-register-birth-abroad', 'data_type': 'journey'},
    {'data_group': 'pay-register-death-abroad', 'data_type': 'journey'},
    {'data_group': 'paye-employee-company-car', 'data_type': 'browser-usage'},
    {'data_group': 'paye-employee-company-car', 'data_type': 'device-usage'},
    {'data_group': 'paye-employee-company-car', 'data_type': 'new-returning-count'},
    {'data_group': 'performance-platform', 'data_type': 'browsers'},
    {'data_group': 'performance-platform', 'data_type': 'devices'},
    {'data_group': 'performance-platform', 'data_type': 'traffic-count'},
    {'data_group': 'police-uk-postcode-search', 'data_type': 'browser-usage'},
    {'data_group': 'police-uk-postcode-search', 'data_type': 'device-usage'},
    {'data_group': 'police-uk-postcode-search', 'data_type': 'new-returning-count'},
    {'data_group': 'prison-visits', 'data_type': 'device-usage'},
    {'data_group': 'prison-visits', 'data_type': 'journey'},
    {'data_group': 'renewtaxcredits', 'data_type': 'device-usage'},
    {'data_group': 'renewtaxcredits', 'data_type': 'journey'},
    {'data_group': 'service-submission-portal', 'data_type': 'browsers'},
    {'data_group': 'service-submission-portal', 'data_type': 'devices'},
    {'data_group': 'service-submission-portal', 'data_type': 'traffic-count'},
    {'data_group': 'student-finance', 'data_type': 'browser-usage'},
    {'data_group': 'student-finance', 'data_type': 'device-usage'},
    {'data_group': 'student-finance', 'data_type': 'journey'},
    {'data_group': 'student-finance', 'data_type': 'new-returning-users'},
    {'data_group': 'student-finance', 'data_type': 'site-traffic'},
    {'data_group': 'tax-vat-content', 'data_type': 'devices-count'},
    {'data_group': 'tax-vat-content', 'data_type': 'new-returning-count'},
    {'data_group': 'tax-vat-content', 'data_type': 'organic-rate'},
    {'data_group': 'tax-vat-content', 'data_type': 'pageviews-count'},
    {'data_group': 'tax-vat-content', 'data_type': 'referrers-rate'},
    {'data_group': 'tax-vat-content', 'data_type': 'social-rate'},
    {'data_group': 'tax-vat-content', 'data_type': 'top-count'},
    {'data_group': 'tax-vat-content', 'data_type': 'traffic-count'},
    {'data_group': 'tier-2-visit-visa', 'data_type': 'devices'},
    {'data_group': 'tier-2-visit-visa', 'data_type': 'journey'},
    {'data_group': 'tier-2-visit-visa', 'data_type': 'volumetrics'},
    {'data_group': 'view-driving-record', 'data_type': 'devices'},
    {'data_group': 'view-driving-record', 'data_type': 'digital-transactions'}
]

if __name__ == '__main__':
    count = 0
    other_timespan = 0
    no_timespan = 0
    no_humanid = 0
    what = 0
    waaaa = 0
    waaaa_stuff = []
    other_timespan_stuff = Set([])
    for group_and_type in groups_and_types:
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
        resp = requests.get(url)
        print 'got'
        data = resp.json()
        for data_point in data['data']:
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
        if this_other_timespan == 0 and not len(data['data']) == 0:
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
    # purge and push too big - need to remove single record and re push

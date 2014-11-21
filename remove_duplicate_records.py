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
    {'data_group': u'govuk-info', 'data_type': u'page-statistics'}
]

total_changed = 0
total_okay_records = 0
no_timespan = 0
no_humanid = 0
i_dont_know_what_this_is = 0
count_of_data_sets_that_may_intentionally_miss_proper_ids = 0
data_sets_that_may_intentionally_miss_proper_ids = []
data_set_changes_dicts = []
may_never_have_had_id_with_timespan = []
incorrectly_formatted_ids = []
capped_collection_error = []
already_fixed = []
timespans_of_okay_records = Set([])


def main_function():

    for group_and_type in groups_and_types:

        def get_config_from_admin_app():
            return admin_api.get_data_set(
                group_and_type['data_group'],
                group_and_type['data_type'])

        def current_mongo_collection():
            return storage._db[data_set_config['name']]

        def data_query(skip=0):
            return current_mongo_collection().find({
                '_updated_at': {
                '$gte': datetime.datetime(2014, 11, 13, 0, 0),
                '$lt': datetime.datetime(2014, 11, 21, 0, 0)}
            }, limit=100, skip=skip, sort=[("_updated_at", pymongo.ASCENDING)])

        def change_data(data):
            #print "top2==================="
            global total_changed
            global total_okay_records
            global no_timespan
            global no_humanid
            global i_dont_know_what_this_is
            global count_of_data_sets_that_may_intentionally_miss_proper_ids
            global data_sets_that_may_intentionally_miss_proper_ids
            global data_set_changes_dicts
            global may_never_have_had_id_with_timespan
            global incorrectly_formatted_ids
            global capped_collection_error
            global already_fixed
            global timespans_of_okay_records
            for data_point in data:

                def no_timespan_in_id():
                    return data_point['timeSpan'] not in data_point['humanId']

                def update_with_ids(the_id, humanId):
                    update = True

                    try:
                        current_mongo_collection().remove(
                            {'_id': data_point['_id']})
                        print "rem"
                    except pymongo.errors.OperationFailure:
                        capped_collection_error.append(data_set_config['name'])
                        update = False
                    if update:
                        print "okat"
                        new_data = data_point
                        new_data['_id'] = the_id
                        new_data['humanId'] = humanId
                        try:
                            current_mongo_collection().insert(new_data)
                            print "ins"
                        except pymongo.errors.DuplicateKeyError:
                            update = False
                            already_fixed.append(data_set_config['name'])
                    return update

                if 'humanId' in data_point and 'timeSpan' in data_point:
                    if no_timespan_in_id():
                        print "==================="
                        print total_changed
                        print total_okay_records
                        print "==================="
                        (the_id, humanId) = generate_id(data_point)
                        if "_{}".format(
                                data_point['timeSpan']) not in humanId:
                            incorrectly_formatted_ids.append(humanId)
                        if update_with_ids(the_id, humanId):
                            total_changed += 1
                        print humanId.encode('utf-8')
                    else:
                        #print "==================="
                        #print total_changed
                        #print total_okay_records
                        #print "==================="
                        total_okay_records += 1
                        timespans_of_okay_records.add(data_point['timeSpan'])
                else:
                    if 'humanId' not in data_point:
                        no_humanid += 1
                    elif 'timeSpan' in data_point:
                        no_timespan += 1
                    else:
                        i_dont_know_what_this_is += 1

        def get_and_update_data_set_data_since_change():
            skip = 0
            data = [i for i in data_query(skip)]
            while(data):
                #print "==========================="
                #print skip
                #print "==========================="
                change_data(data)
                skip += 100
                data = [i for i in data_query(skip)]

        print "getting config"
        data_set_config = get_config_from_admin_app()
        print "got"

        get_and_update_data_set_data_since_change()

    print "COUNTS"
    print {
        'total_changed': total_changed,
        'total_okay_records': total_okay_records,
        'no_timespan': no_timespan,
        'no_humanid': no_humanid,
        'i_dont_know_what_this_is': i_dont_know_what_this_is,
        'count_of_data_sets_that_may_intentionally_miss_proper_ids': count_of_data_sets_that_may_intentionally_miss_proper_ids}
    print "timespans_of_okay_records=================="
    print timespans_of_okay_records
    print "data_sets_that_may_intentionally_miss_proper_ids=================="
    print("these are all collected since"
          "they may correctly have no proper id but it seems unlikely, they get overwritten during a run, check the config but we can be pretty sure it's okay")
    print data_sets_that_may_intentionally_miss_proper_ids
    print "data_set_changes_dicts=================="
    print data_set_changes_dicts
    print "incorrectly_formatted_ids=================="
    print incorrectly_formatted_ids
    print len(incorrectly_formatted_ids)
    print "capped_collection_error=================="
    print capped_collection_error
    print len(capped_collection_error)
    print "already_fixed=================="
    print already_fixed
    print len(already_fixed)

if __name__ == '__main__':
    main_function()

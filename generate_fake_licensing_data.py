import datetime
import json
from random import choice, randint
from pymongo import MongoClient
import sys

HOST = 'localhost'
PORT = 27017
DB_NAME = 'backdrop'
BUCKET = 'licensing'

# IMPORTANT:
#
# Dates are required to be stored as ISODate so you need to run these
# postprocessing scripts after loading data into db:
#
# /usr/bin/mongo your_database --eval "
#   db.your_collection.find({ _timestamp: { \$type: 2}}).forEach(
#     function(doc){
#       doc._timestamp = new ISODate(doc._timestamp);
#       db.your_collection.save(doc)
#     });"
#
# /usr/bin/mongo your_database --eval "
#   db.your_collection.find({ _week_start_at: { \$type: 2}}).forEach(
#     function(doc){
#       doc._week_start_at = new ISODate(doc._week_start_at);
#       db.your_collection.save(doc)
#     });"

USAGE = """
./generate_fake_licensing_data.py (save_to_db|print_json)
"""


def find_last_monday():
    now = datetime.datetime.now().replace(hour=0, minute=0, second=0,
                                          microsecond=0)
    return now - datetime.timedelta(days=now.weekday())


def generate_last_n_mondays(n):
    last_monday = find_last_monday()
    n_mondays = []
    for i in range(0, n):
        n_mondays.append(last_monday - (i * datetime.timedelta(days=7)))
    n_mondays.reverse()
    return n_mondays


def select_random_Monday():
    dates_to_use = generate_last_n_mondays(9)
    return choice(dates_to_use)


def select_random_authority():
    authorities = [
        "Fakesville",
        "NoSuchTown",
        "TestPort",
        "Nowhere-on-sea",
        "Not-a-real-place",
    ]
    return choice(authorities)


def licence_event():
    some_monday = select_random_Monday()
    return {
        'dataType': 'licenceApplication',
        '_week_start_at': some_monday,
        '_timestamp': some_monday + datetime.timedelta(days=randint(0, 6)),
        '_id': 'fake-%i' % i
    }


def authority():
    authority_name = select_random_authority()
    return {
        'authorityUrlSlug': authority_name.lower(),
        'authorityName': 'City of %s Council' % authority_name
    }


def select_random_licence():
    licences = [
        {'name': 'Fake Licence 1', 'code': '1111-1-1', 'payment': True},
        {'name': 'Fake Licence 2', 'code': '1111-2-1', 'payment': True},
        {'name': 'Fake Licence 3', 'code': '1111-3-1', 'payment': False},
        {'name': 'Fake Licence 4', 'code': '1111-3-1', 'payment': True},
        {'name': 'Fake Licence 5', 'code': '1111-3-1', 'payment': False},
        {'name': 'Fake Licence 6', 'code': '1111-3-1', 'payment': False},
    ]
    return choice(licences)


def generate_payment_status(payment):
    if payment:
        return choice(['Unknown', 'Success'])
    else:
        return ""


def licence():
    selected_licence = select_random_licence()
    return {
        'licenceUrlSlug': selected_licence['name'].lower().replace(' ', '-'),
        'licenceCode': selected_licence['code'],
        'licenceName': selected_licence['name'],
        'isPaymentRequired': selected_licence['payment'],
        'paymentStatus': generate_payment_status(selected_licence['payment'])
    }


def select_random_interaction():
    interactions = [
        {'action': 'apply', 'code': 1},
        {'action': 'renew', 'code': 2},
        {'action': 'change', 'code': 3},
    ]
    return choice(interactions)


def interaction(licence_name):
    selected_interaction = select_random_interaction()
    return {
        'licenceInteractionName': "%s for a %s" % (
        selected_interaction['action'],
        licence_name),
        'licenceInteractionlgilId': selected_interaction['action'],
        'licenceInteractionlgilSubId': selected_interaction['code']
    }


def time_to_str(time):
    return time.strftime('%Y-%m-%dT%H:%M:%S')


if len(sys.argv) < 2:
    print USAGE
    sys.exit(1)

if __name__ == "__main__":
    argument = sys.argv[1]

    licence_apps = []

    for i in range(0, 10000):
        licence_application = {}
        licence_application.update(licence_event())
        licence_application.update(authority())
        licence_application.update(licence())
        licence_application.update(
            interaction(licence_application['licenceName']))
        licence_apps.append(licence_application)

    if argument == "save_to_db":
        for application in licence_apps:
            MongoClient(HOST, PORT)[DB_NAME][BUCKET].save(application)
        sys.exit(0)

    elif argument == "print_json":
        for application in licence_apps:
            application['_timestamp'] = time_to_str(application['_timestamp'])
            application['_week_start_at'] = \
                time_to_str(application['_week_start_at'])
        for application in licence_apps:
            print json.dumps(application)
        sys.exit(0)

    else:
        print USAGE
        sys.exit(1)

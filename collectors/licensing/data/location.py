import datetime
import httplib2

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run

class Locations(object):
    CLIENT_SECRETS_FILE = 'client_secrets.json'

    FLOW = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
        scope = "https://www.googleapis.com/auth/analytics.readonly",
        message = "Something seems to have gone wrong, check the client secrets file")
    
    def __init__(self):    
        storage = Storage("tokens.dat")
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = run(self.FLOW, storage)

        http = httplib2.Http()
        http = credentials.authorize(http)

        service = build("analytics","v3", http = http)

        first_date, last_date = get_last_whole_month(datetime.date.today())
        query = service.data().ga().get(
            metrics = "ga:visits",
            dimensions = "ga:pagePath,ga:country",
            max_results = "5000",
            start_date = first_date.strftime('%Y-%m-%d'),
            end_date = last_date.strftime('%Y-%m-%d'),
            ids = "ga:63654109",
            filters = "ga:pagePath=~^/apply-for-a-licence/.*/form$")
        
        response = query.execute()
        
        self.results = response["rows"]
        self.start_date = response["query"]["start-date"]
        self.end_date = response["query"]["end-date"]

def get_last_whole_month(date):
    last_date = first_day_of_month(date) - datetime.timedelta(days=1)
    first_date = first_day_of_month(last_date)

    return first_date, last_date

def first_day_of_month(date):
    return datetime.date(year=date.year, month=date.month, day=1)

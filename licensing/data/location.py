import httplib2
import json
import itertools
from collections import defaultdict

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
            credentials = run(FLOW, storage)

        http = httplib2.Http()
        http = credentials.authorize(http)

        service = build("analytics","v3", http = http)

        query = service.data().ga().get(
            metrics = "ga:visits",
            dimensions = "ga:pagePath,ga:country",
            max_results = "5000",
            start_date = "2013-01-01",
            end_date = "2013-02-01",
            ids = "ga:63654109",
            filters = "ga:pagePath=~^/apply-for-a-licence/.*/form$")
        
        response = query.execute()['rows']
        
        self.results = response
        

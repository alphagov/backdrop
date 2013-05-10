from pymongo import MongoClient
from splinter import Browser
from features.support.http_test_client import HTTPTestClient


class SplinterClient(object):

    def __init__(self, database_name):
        self.database_name = database_name
        self.browser = Browser('phantomjs')
        self.http_test_client = HTTPTestClient(database_name)

    def storage(self):
        return MongoClient('localhost', 27017)[self.database_name]

    def spin_down(self):
        self.http_test_client.spin_down()
        self.browser.quit()

    def get(self, url, headers=None):
        self.browser.visit(self.http_test_client.write_url(url))
        return SplinterResponse(self.browser)


class SplinterResponse:
    def __init__(self, browser):
        self.status_code = browser.status_code
        self.data = None
        self.headers = None
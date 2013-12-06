from datetime import datetime
import logging
from pymongo import MongoClient
from splinter import Browser

from features.support.support import Api, BaseClient


logger = logging.getLogger(__name__)


class SplinterClient(BaseClient):

    def __init__(self, database_name):
        self.database_name = database_name
        self._write_api = Api.start_api('write', '5001')

    def storage(self):
        return MongoClient('localhost', 27017)[self.database_name]

    def before_scenario(self):
        self.browser = Browser('phantomjs', wait_time=3)

    def after_scenario(self, scenario):
        if scenario.status == 'failed':
            self._save_screenshot(self._screenshot_name(scenario.name))
        self.browser.quit()

    def spin_down(self):
        self._write_api.stop()

    def get(self, url, headers=None):
        self.browser.visit(self._write_api.url(url))
        return SplinterResponse(self.browser)

    def _screenshot_name(self, scenario_name):
        return "tmp/screenshot_%s_%s.png" % (
            datetime.now().isoformat(), scenario_name.replace(' ', '_'))

    def _save_screenshot(self, filename):
        try:
            success = self.browser.driver.save_screenshot(filename)
            if not success:
                logger.warn(
                    "Unable to save screenshot %s: IO error" % filename)
        except Exception as e:
            logger.warn("Unable to save screenshot %s: Exception" % filename)
            logger.warn(e)


class SplinterResponse:
    def __init__(self, browser):
        self.status_code = browser.status_code
        self.data = None
        self.headers = dict(browser.response.getheaders())

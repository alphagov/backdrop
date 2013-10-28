from hamcrest import assert_that, has_entries
import os
import logging
import json
from backdrop.core import log_handler
import unittest
from flask import Flask


class TestJsonLogging(unittest.TestCase):

    def setUp(self):
        self.app = Flask('json_test_app')
        self.logger = self.app.logger
        self.app.config['LOG_LEVEL'] = logging.DEBUG

    def test_json_log_written_when_logger_called(self):

        log_handler.set_up_logging(self.app, 'json_test', 'json_test')
        self.logger.info('Writing out JSON formatted logs m8')

        with open('log/json_test.log.json') as log_file:
            data = json.loads(log_file.readlines()[-1])

        assert_that(data, has_entries({
            '@message': 'Writing out JSON formatted logs m8'
        }))

        assert_that(data, has_entries({
            '@tags': ['application']
        }))

        # Only remove file if assertion passes
        os.remove('log/json_test.log.json')
        os.remove('log/json_test.log')

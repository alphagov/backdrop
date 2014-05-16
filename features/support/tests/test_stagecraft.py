import requests
from requests.exceptions import ConnectionError
from nose.tools import assert_raises
from hamcrest import assert_that, is_

from ..stagecraft import StagecraftService

class TestStagecraftService(object):
    def create_service(self):
        return StagecraftService(8089, {
            ('GET', u'example'): {u'foo': u'bar'}
        })

    def test_service_catches_calls(self):
        service = self.create_service()
        service.start()
        response = requests.get('http://localhost:8089/example')
        service.stop()
       
        assert_that(response.json(), is_({u'foo': u'bar'}))

    def test_calls_fail_if_service_is_not_started(self):
        self.create_service()
        assert_raises(ConnectionError, requests.get, ('http://localhost:8089/example'))

    def test_calls_fail_after_service_is_stopped(self):
        service = self.create_service()
        service.start()
        service.stop()
        assert_raises(ConnectionError, requests.get, ('http://localhost:8089/example'))

    def test_running_returns_true_if_the_service_is_running(self):
        service = self.create_service()
        assert_that(service.running(), is_(False))
        service.start()
        assert_that(service.running(), is_(True))
        service.stop()
        assert_that(service.running(), is_(False))

    def test_stopped_returns_true_if_the_service_is_not_running(self):
        service = self.create_service()
        assert_that(service.stopped(), is_(True))
        service.start()
        assert_that(service.stopped(), is_(False))
        service.stop()
        assert_that(service.stopped(), is_(True))


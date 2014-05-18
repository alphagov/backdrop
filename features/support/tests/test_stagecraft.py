import requests
from requests.exceptions import ConnectionError
from nose.tools import assert_raises
from hamcrest import assert_that, is_

from ..stagecraft import StagecraftService, create_or_update_stagecraft_service, stop_stagecraft_service_if_running


class StubContext(object):
    def __init__(self):
        self._params = {}

    def __getattr__(self, key):
        return self._params[key]

    def __setattr__(self, key, value):
        if key.startswith('_'):
            self.__dict__[key] = value
        else:
            self._params[key] = value

    def __contains__(self, key):
        return key in self._params

def test_create_stagecraft_service():
    context = StubContext()
    service = create_or_update_stagecraft_service(context, 2012, {})

    assert_that(context.mock_stagecraft_service.running(), is_(True))

    service.stop()

    assert_that(context.mock_stagecraft_service.stopped(), is_(True))


def test_update_stagecraft_service():
    context = StubContext()

    service1 = create_or_update_stagecraft_service(context, 8089, {})
    response = requests.get('http://localhost:8089/example')
    assert_that(response.status_code, is_(404))

    service2 = create_or_update_stagecraft_service(context, 8089,
        {('GET', u'example'): {u'foo': u'bar'}})
    response = requests.get('http://localhost:8089/example')
    assert_that(response.status_code, is_(200))

    assert_that(service1, is_(service2))

    service1.stop()


def test_stop_stagecraft_if_running():
    context = StubContext()

    service = create_or_update_stagecraft_service(context, 8089, {})

    stop_stagecraft_service_if_running(context)

    assert_that(service.running(), is_(False))

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

    def test_calls_succeed_after_service_is_restarted(self):
        service = self.create_service()
        service.restart()

        response = requests.get('http://localhost:8089/example')

        service.stop()
        assert_that(response.status_code, is_(200))

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

    def test_new_routes_can_be_added_to_a_running_service(self):
        service = self.create_service()
        service.start()
        service.add_routes({
            ('GET', u'foobar'): {u'bar': u'foo'}})

        response = requests.get('http://localhost:8089/foobar')

        service.stop()

        assert_that(response.json(), is_({u'bar': u'foo'}))

    def test_all_routes_can_be_removed_from_a_running_service(self):
        service = self.create_service()
        service.start()
        service.reset()
        response = requests.get('http://localhost:8089/example')
        service.stop()

        assert_that(response.status_code, is_(404))

from mock import Mock
from backdrop import StatsClient


class TestStatsd(object):
    def setup(self):
        self.client = Mock()
        self.wrapper = StatsClient(self.client)

    def test_timer(self):
        self.wrapper.timer('foo.bar', data_set='monkey')
        self.client.timer.assert_called_with('monkey.foo.bar')

    def test_timing(self):
        self.wrapper.timing('foo.bar', 10, data_set='monkey')
        self.client.timing.assert_called_with('monkey.foo.bar', 10)

    def test_incr(self):
        self.wrapper.incr('foo.bar', data_set='monkey')
        self.client.incr.assert_called_with('monkey.foo.bar')

    def test_decr(self):
        self.wrapper.decr('foo.bar', data_set='monkey')
        self.client.decr.assert_called_with('monkey.foo.bar')

    def test_gauge(self):
        self.wrapper.gauge('foo.bar', 123, data_set='monkey')
        self.client.gauge.assert_called_with('monkey.foo.bar', 123)

    def test_should_prefix_unknown_when_no_data_set_is_provided(self):
        self.wrapper.incr('foo.bar')
        self.client.incr.assert_called_with('unknown.foo.bar')

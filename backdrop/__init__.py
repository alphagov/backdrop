import os
import statsd as _statsd


__all__ = ['statsd']


class StatsClient(object):
    """Wrap statsd.StatsClient to allow data_set to be added to stat"""
    def __init__(self, statsd):
        self._statsd = statsd

    def __getattr__(self, item):
        if item in ['timer', 'timing', 'incr', 'decr', 'gauge']:
            def func(stat, *args, **kwargs):
                data_set = kwargs.pop('data_set', 'unknown')
                stat = '%s.%s' % (data_set, stat)

                return getattr(self._statsd, item)(stat, *args, **kwargs)
            return func
        else:
            return getattr(self._statsd, item)

statsd = StatsClient(
    _statsd.StatsClient(prefix=os.getenv(
        "GOVUK_STATSD_PREFIX", "pp.apps.backdrop")))

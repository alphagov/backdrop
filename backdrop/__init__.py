import os
import statsd as _statsd


__all__ = ['statsd']

statsd = _statsd.StatsClient(prefix=os.getenv("GOVUK_STATSD_PREFIX"))

from collections import namedtuple

from .timeutils import now


"""
This is the internal Query object
 - Create list of attributes to build the query from
 - We use delta internally, but the end user will use 'duration'
"""
_Query = namedtuple(
    '_Query',
    ['start_at', 'end_at', 'delta', 'period',
     'filter_by', 'filter_by_prefix', 'group_by', 'sort_by', 'limit',
     'collect', 'flatten', 'inclusive'])


class Query(_Query):

    @classmethod
    def create(cls,
               start_at=None, end_at=None, duration=None, delta=None,
               period=None, filter_by=None, filter_by_prefix=None,
               group_by=None, sort_by=None, limit=None, collect=None,
               flatten=None, inclusive=None):
        delta = None
        if duration is not None:
            date = start_at or end_at or now()
            delta = duration if start_at else -duration
            start_at, end_at = cls.__calculate_start_and_end(period, date,
                                                             delta)
        return Query(start_at, end_at, delta, period, filter_by or [],
                     filter_by_prefix or [], group_by or [], sort_by, limit,
                     collect or [], flatten, inclusive)

    @staticmethod
    def __calculate_start_and_end(period, date, delta):
        duration = period.delta * delta
        start_of_period = period.start(date)

        start_at, end_at = sorted(
            [start_of_period, start_of_period + duration])

        return start_at, end_at

    @property
    def collect_fields(self):
        """Return a unique list of collect field names
        >>> query = Query.create(collect=[('foo', 'sum'), ('foo', 'set')])
        >>> query.collect_fields
        ['foo']
        """
        return list(set([field for field, _ in self.collect]))

    @property
    def group_keys(self):
        """Return a list of lists of combinations of fields that are being
        grouped on

        This is kinda coupled to how we group with Mongo but these keys
        are in the returned results and are used in the nested merge to
        create the hierarchical response.

        >>> from ..core.timeseries import WEEK
        >>> Query.create(group_by=['foo']).group_keys
        [['foo']]
        >>> Query.create(period=WEEK).group_keys
        [['_week_start_at']]
        >>> Query.create(group_by=['foo'], period=WEEK).group_keys
        [['foo'], ['_week_start_at']]
        """
        keys = []
        if self.group_by:
            keys.append(self.group_by)
        if self.period:
            keys.append([self.period.start_at_key])
        return keys

    @property
    def is_grouped(self):
        """
        >>> Query.create(group_by="foo").is_grouped
        True
        >>> Query.create(period="week").is_grouped
        True
        >>> Query.create().is_grouped
        False
        """
        return bool(self.group_by) or bool(self.period)

    def get_shifted_query(self, shift):
        """Return a new Query where the date is shifted by n periods"""
        args = self._asdict()

        args['start_at'] = args['start_at'] + (self.period.delta * shift)
        args['end_at'] = args['end_at'] + (self.period.delta * shift)

        return Query.create(**args)

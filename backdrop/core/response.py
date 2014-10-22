import pytz
from backdrop.core.nested_merge import collect_key
from backdrop.core.timeseries import timeseries, PERIODS
from flask import make_response
from functools import update_wrapper


def create_period_group(doc, period):
    if period.start_at_key not in doc or "_count" not in doc:
        raise ValueError("Expected subgroup to have keys '_count'"
                         " and '{}'".format(period.start_at_key))

    datum = doc.copy()

    start_at = datum.pop(period.start_at_key).replace(tzinfo=pytz.utc)

    if not period.valid_start_at(start_at):
        raise ValueError(
            "Invalid {} start: {}".format(period.name, start_at))

    datum['_start_at'] = start_at
    datum['_end_at'] = start_at + period.delta

    return datum


def first_nonempty(data, is_reversed):
    if is_reversed:
        data = reversed(data)

    # iterate through data and get the index of the first non-empty result
    first_nonempty_index = next(
        (i for i, d in enumerate(data) if d['_count'] > 0),
        0)

    if is_reversed:
        first_nonempty_index = -first_nonempty_index

    return first_nonempty_index


class SimpleData(object):

    def __init__(self, cursor):
        self._data = []
        for doc in cursor:
            self.__add(doc)

    def __add(self, document):
        if "_timestamp" in document:
            document["_timestamp"] = \
                document["_timestamp"].replace(tzinfo=pytz.utc)
        self._data.append(document)

    def data(self):
        return tuple(self._data)

    def amount_to_shift(self, delta):
        """This response type cannot be shifted"""
        return 0


class PeriodData(object):

    def __init__(self, cursor, period):
        self.period = period
        self._data = []
        for doc in cursor:
            self.__add(doc)

    def __add(self, document):
        self._data.append(self.__create_datum(document))

    def data(self):
        return tuple(self._data)

    def fill_missing_periods(self, start_date, end_date, collect=None):
        default = {"_count": 0}
        if collect:
            default.update((collect_key(k, v), None) for k, v in collect)
        self._data = timeseries(start=start_date,
                                end=end_date,
                                period=self.period,
                                data=self._data,
                                default=default)

    def __create_datum(self, doc):
        datum = create_period_group(doc, self.period)

        for period in PERIODS:
            doc.pop(period.start_at_key, None)

        return dict(datum.items() + doc.items())

    def amount_to_shift(self, delta):
        is_reversed = delta < 0

        return first_nonempty(self._data, is_reversed)


class GroupedData(object):

    def __init__(self, cursor):
        self._data = []
        for doc in cursor:
            self.__add(doc)

    def __add(self, document):
        self._data.append(document)

    def data(self):
        return tuple(self._data)

    def amount_to_shift(self, delta):
        """This response type cannot be shifted"""
        return 0


class FlatData(object):

    def __init__(self, cursor):
        self._data = []
        for doc in cursor:
            self.__add(doc)

    def __add(self, document):
        self._data.append(document)

    def data(self):
        return tuple(self._data)

    def amount_to_shift(self, delta):
        """This response type cannot be shifted"""
        return 0


class PeriodGroupedData(object):

    def __init__(self, cursor, period):
        self._period = period
        self._data = []
        for doc in cursor:
            self._add(doc)

    def _create_subgroup(self, subgroup):
        return create_period_group(subgroup, self._period)

    def _add(self, group):
        if '_subgroup' not in group:
            raise ValueError("Expected group to have key '_subgroup'")

        datum = {}
        datum['values'] = [
            self._create_subgroup(subgroup) for subgroup in group["_subgroup"]]
        datum.update(
            (key, value) for key, value in group.items() if key != '_subgroup')

        self._data.append(datum)

    def data(self):
        return tuple(self._data)

    def fill_missing_periods(self, start_date, end_date, collect=None):
        default = {"_count": 0}
        if collect:
            default.update((collect_key(k, v), None) for k, v in collect)
        for i, _ in enumerate(self._data):
            self._data[i]['values'] = timeseries(
                start=start_date,
                end=end_date,
                period=self._period,
                data=self._data[i]['values'],
                default=default
            )

    def amount_to_shift(self, delta):
        is_reversed = delta < 0

        if len(self._data) == 0:
            return 0

        return min(
            [first_nonempty(i['values'], is_reversed) for i in self._data],
            key=abs)


class PeriodFlatData(object):

    def __init__(self, cursor, period):
        self._period = period
        self._data = []
        for doc in cursor:
            self._add(doc)

    def _add(self, document):
        datum = create_period_group(document, self._period)
        self._data.append(datum)

    def data(self):
        return tuple(self._data)

    def fill_missing_periods(self, start_date, end_date, collect=None):
        default = {"_count": 0}
        if collect:
            default.update((collect_key(k, v), None) for k, v in collect)
        self._data = timeseries(start=start_date,
                                end=end_date,
                                period=self._period,
                                data=self._data,
                                default=default)

    def amount_to_shift(self, delta):
        is_reversed = delta < 0

        if len(self._data) == 0:
            return 0

        return first_nonempty(self._data, is_reversed)


def crossdomain(origin=None):
    """
    See: http://flask.pocoo.org/snippets/56/
    Example usage:
        @crossdomain(origin='*')
        def my_service():
            return jsonify(foo='cross domain ftw')
    """

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            resp = make_response(f(*args, **kwargs))
            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            return resp
        return update_wrapper(wrapped_function, f)
    return decorator

import datetime
import pytz
from backdrop.core.timeseries import timeseries, WEEK, MONTH
from dateutil.relativedelta import relativedelta


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

    def fill_missing_periods(self, start, end):
        self._data = timeseries(start=start,
                                end=end,
                                period=self.period,
                                data=self._data,
                                default={"_count": 0})

    def __create_datum(self, doc):
        datum = {}
        datum = create_period_group(doc, self.period)

        for key in ["_week_start_at", "_month_start_at"]:
            doc.pop(key, None)

        return dict(datum.items() + doc.items())


class GroupedData(object):
    def __init__(self, cursor):
        self._data = []
        for doc in cursor:
            self.__add(doc)

    def __add(self, document):
        self._data.append(document)

    def data(self):
        return tuple(self._data)


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

    def fill_missing_periods(self, start_date, end_date):
        for i, _ in enumerate(self._data):
            self._data[i]['values'] = timeseries(
                start=start_date,
                end=end_date,
                period=self._period,
                data=self._data[i]['values'],
                default={"_count": 0}
            )

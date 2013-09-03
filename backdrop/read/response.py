import datetime
import pytz
from backdrop.core.timeseries import timeseries, WEEK, MONTH
from dateutil.relativedelta import relativedelta


def create_period_group(doc):
    if "_week_start_at" not in doc or "_count" not in doc:
        raise ValueError("Expected subgroup to have keys '_count'"
                         " and '_week_start_at'")
    if doc["_week_start_at"].weekday() is not 0:
        raise ValueError("Weeks MUST start on Monday but "
                         "got date: %s" % doc["_week_start_at"])
    datum = doc.copy()
    datum["_start_at"] = datum.pop("_week_start_at").replace(tzinfo=pytz.utc)
    datum["_end_at"] = datum["_start_at"] + datetime.timedelta(days=7)
    return datum


def create_period_group_month(doc):
    if "_month_start_at" not in doc or "_count" not in doc:
        raise ValueError("Expected subgroup to have keys '_count' and "
                         "'_month_start_at'")
    if doc["_month_start_at"].day != 1:
        raise ValueError("Months MUST start on the 1st but "
                         "got date: %s" % doc["_month_start_at"])
    datum = doc.copy()
    datum["_start_at"] = datum.pop("_month_start_at").replace(tzinfo=pytz.utc)
    datum["_end_at"] = (datum["_start_at"]
                        + relativedelta(months=1)).replace(tzinfo=pytz.UTC)
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
        periods = {
            "week": WEEK,
            "month": MONTH
        }
        self._data = timeseries(start=start,
                                end=end,
                                period=periods[self.period],
                                data=self._data,
                                default={"_count": 0})

    def __create_datum(self, doc):
        datum = {}
        if self.period == "week":
            datum = create_period_group(doc)
        if self.period == "month":
            datum = create_period_group_month(doc)

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
    def __init__(self, cursor, period, data_factory):
        self._period = period
        self._data_factory = data_factory
        self._data = []
        for doc in cursor:
            self._add(doc)

    def _add(self, group):
        if '_subgroup' not in group:
            raise ValueError("Expected group to have key '_subgroup'")

        datum = {}
        datum['values'] = [
            self._data_factory(subgroup) for subgroup in group["_subgroup"]]
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


class WeeklyGroupedData(PeriodGroupedData):
    def __init__(self, cursor):
        super(WeeklyGroupedData, self).__init__(
            cursor, WEEK, create_period_group)


class MonthlyGroupedData(PeriodGroupedData):
    def __init__(self, cursor):
        super(MonthlyGroupedData, self).__init__(
            cursor, MONTH, create_period_group_month)

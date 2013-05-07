import datetime
import pytz
from backdrop.core.timeseries import timeseries, WEEK

def create_period_group(doc):
    if "_week_start_at" not in doc or "_count" not in doc:
        raise ValueError("Expected subgroup to have keys '_count'"
                         " and '_week_start_at'")
    if doc["_week_start_at"].weekday() is not 0:
        raise ValueError("Weeks MUST start on Monday but "
                         "got date: %s" % doc["_week_start_at"])
    datum = {}
    datum["_start_at"] = doc["_week_start_at"].replace(tzinfo=pytz.utc)
    datum["_end_at"] = datum["_start_at"] + datetime.timedelta(days=7)
    datum["_count"] = doc["_count"]
    return datum

class SimpleData(object):
    def __init__(self):
        self._data = []

    def add(self, document):
        if "_timestamp" in document:
            document["_timestamp"] = \
                document["_timestamp"].replace(tzinfo=pytz.utc)
        self._data.append(document)

    def data(self):
        return tuple(self._data)


class PeriodData(object):
    def __init__(self):
        self._data = []

    def add(self, document):
        self._data.append(self.__create_datum(document))

    def data(self):
        return tuple(self._data)

    def fill_missing_weeks(self, start, end):
        self._data = timeseries(start=start,
                                end=end,
                                period=WEEK,
                                data=self._data,
                                default={"_count": 0})

    def __create_datum(self, doc):
        datum = create_period_group(doc)
        return datum


class WeeklyGroupedData(object):
    def __init__(self):
        self._data = []

    def add(self, datum):
        if "_subgroup" not in datum:
            raise ValueError("Expected document to have key '_subgroup'")

        _datum = {}
        _datum.update({"values":
                           [create_period_group(entry)
                            for entry
                            in datum["_subgroup"]]})
        self._data.append(_datum)

    def data(self):
        return tuple(self._data)
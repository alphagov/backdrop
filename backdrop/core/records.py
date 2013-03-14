import datetime


class Record(object):

    def __init__(self, data):
        self.data = data
        self.meta = {}
        if "_timestamp" in self.data:
            days_since_week_start = datetime.timedelta(
                days=self.data['_timestamp'].weekday())
            week_start = self.data['_timestamp'] - days_since_week_start
            self.meta['_week_start_at'] = week_start.replace(
                hour=0, minute=0, second=0, microsecond=0)

    def to_mongo(self):
        return dict(
            self.data.items() + self.meta.items()
        )

    def __eq__(self, other):
        if not isinstance(other, Record):
            return False
        if self.data != other.data:
            return False
        if self.meta != other.meta:
            return False
        return True

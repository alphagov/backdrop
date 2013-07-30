from datetime import timedelta, datetime
import itertools
from tests.support.test_helpers import d_tz


def ceg_volumes(rows):
    yield _ceg_keys(rows)

    for row in _ceg_rows(rows):
        yield row


def _ceg_keys(rows):
    return [
        "_timestamp", "timeSpan", "relicensing_web", "relicensing_ivr",
        "relicensing_agent", "sorn_web", "sorn_ivr", "sorn_agent",
        "agent_automated_dupes", "calls_answered_by_advisor"
    ]


def _ceg_rows(rows):
    for column in itertools.count(3):
        date = _ceg_date(rows, column)
        if not isinstance(date, datetime):
            return
        if date >= d_tz(2012, 4, 1):
            yield [
                date, "month", rows[5][column], rows[6][column],
                rows[9][column], rows[11][column], rows[12][column],
                rows[13][column], rows[15][column], rows[17][column]
            ]


def _ceg_date(rows, column):
    try:
        return rows[3][column]
    except IndexError:
        return None

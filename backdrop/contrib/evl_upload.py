from datetime import datetime
import itertools


def ceg_volumes(rows):
    """Electronic Vehicle Licensing (EVL) Customer Enquiries Group (CEG)

    Call center volume data

    http://goo.gl/52VcMe
    """
    def ceg_keys(rows):
        return [
            "_timestamp", "timeSpan", "relicensing_web", "relicensing_ivr",
            "relicensing_agent", "sorn_web", "sorn_ivr", "sorn_agent",
            "agent_automated_dupes", "calls_answered_by_advisor"
        ]

    def ceg_rows(rows):
        rows = list(rows)
        for column in itertools.count(3):
            date = ceg_date(rows, column)
            if not isinstance(date, datetime):
                return
            yield [
                date, "month", rows[5][column], rows[6][column],
                rows[9][column], rows[11][column], rows[12][column],
                rows[13][column], rows[15][column], rows[17][column]
            ]

    def ceg_date(rows, column):
        try:
            return rows[3][column]
        except IndexError:
            return None

    yield ceg_keys(rows)

    for row in ceg_rows(rows):
        yield row

from datetime import datetime
import itertools


def ceg_volumes(rows):
    """Electronic Vehicle Licensing (EVL) Customer Enquiries Group (CEG)

    Call center volume data

    http://goo.gl/52VcMe
    """
    RELICENSING_WEB_INDEX = 5
    RELICENSING_IVR_INDEX = 6
    RELICENSING_AGENT_INDEX = 9
    SORN_WEB_INDEX = 11
    SORN_IVR_INDEX = 12
    SORN_AGENT_INDEX = 13
    AGENT_AUTOMATED_DUPES_INDEX = 15
    CALLS_ANSWERED_BY_ADVISOR_INDEX = 17

    ceg_keys = [
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
                date, "month",
                rows[RELICENSING_WEB_INDEX][column],
                rows[RELICENSING_IVR_INDEX][column],
                rows[RELICENSING_AGENT_INDEX][column],
                rows[SORN_WEB_INDEX][column],
                rows[SORN_IVR_INDEX][column],
                rows[SORN_AGENT_INDEX][column],
                rows[AGENT_AUTOMATED_DUPES_INDEX][column],
                rows[CALLS_ANSWERED_BY_ADVISOR_INDEX][column],
            ]

    def ceg_date(rows, column):
        try:
            return rows[3][column]
        except IndexError:
            return None

    yield ceg_keys

    for row in ceg_rows(rows):
        yield row


def service_volumetrics(rows):
    rows = list(rows)
    yield ["_timestamp", "timeSpan", "successful_tax_disc", "successful_sorn"]

    timestamp = rows[2][1]
    taxDiskApplications = rows[24][2]
    sornApplications = rows[25][2]

    yield [timestamp, "day", taxDiskApplications, sornApplications]


def service_failures(sheets):
    rows = list(list(sheets)[1])
    timestamp = rows[1][1]

    yield ["_timestamp", "_id", "type", "reason", "count", "description"]

    def failure(service_type, reason_code, num_failures, description, timestamp):
        return [timestamp, "%s.%s.%s" % (timestamp.date().isoformat(), service_type, reason_code),
                service_type, reason_code, num_failures, description]

    for row in rows[6:]:
        description = row[0]
        if len(description) == 0:
            return

        reason_code = int(row[1])
        tax_disc_failures = int(row[2] or 0)
        sorn_failures = int(row[4] or 0)

        yield failure("tax-disc", reason_code, tax_disc_failures, description, timestamp)
        yield failure("sorn", reason_code, sorn_failures, description, timestamp)

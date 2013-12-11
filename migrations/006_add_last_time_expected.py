"""
Add last time we expected to get data to buckets - max age expected

data types at the time of writing this

    "journey",
    "monitoring",
    "realtime",
    "channels",
    "customer-satisfaction",
    "failures",
    "services",
    "volumetrics",
    "annotations",
    "volumes",
    "application",
    "test",
    "search-volumetrics",
    "annual-mortgage-lending",
    "monthly-mortgage-lending",
    "dwellings-completes",
    "dwellings-starts",
    "first-time-buyer",
    "house-price-index",
    "residential-transactions"

"""
import logging

log = logging.getLogger(__name__)


def up(db):
    all_buckets = db.get_collection('buckets').find()
    for bucket in all_buckets:
        if 'max_age_expected' in bucket:
            continue
        max_age_expected = calculate_max_age(bucket)
        bucket['max_age_expected'] = max_age_expected
        log.info("Adding max age of: %s to %s bucket" %
                 (max_age_expected, bucket['name']))
        db['buckets'].save(bucket)


def calculate_max_age(bucket):
    dt = bucket['data_type']

    dead_buckets = [
        'evl_channel_volumetrics',
        'government_annotations',
        'land_registry_search_volumetrics',
        'hmrc_preview',
        'housing_policy_annual_mortgage_lending',
        'housing_policy_monthly_mortgage_lending'
    ]

    if bucket in dead_buckets:
        return None

    return {
        'realtime': minutes(5),  # 5mins for realtime buckets
        'journey': hours(25),  # Journey buckets should update daily
        # Jobs run every hour, we're giving 2hrs tolerance
        'monitoring': hours(2),
    }.get(dt, months(1))  # default to a month


def months(months):
    # Possibly not the most accurate comparison ever written.
    return months * hours(24) * 31


def hours(hours):
    return hours * (60 * 60)


def minutes(minutes):
    return minutes * 60

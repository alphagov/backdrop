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
        max_age_expected = calculate_max_age(bucket)
        if max_age_expected != bucket['max_age_expected']:
            bucket['max_age_expected'] = max_age_expected
            log.info("Adding max age of: %s to %s bucket" %
                     (max_age_expected, bucket['name']))
            db.get_collection('buckets').save(bucket)


def calculate_max_age(bucket):
    max_ages_for_field = {
        'name': {
            # These buckets are dead
            'evl_channel_volumetrics': None,
            'evl_services_volumetrics': None,
            'gcloud_proportion_sme': None,
            'government_annotations': None,
            'land_registry_search_volumetrics': None,
            'hmrc_preview': None,
            'deposit_foreign_marriage_monitoring': None,
            'deposit_foreign_marriage_realtime': None,
            'deposit_foreign_marriage_journey': None,
            'twilio_prototype': None,
        },
        'data_group': {
            # Housing is not receiving any more data
            'housing-policy': None,
            # Student finance is not receiving data yet
            'student-finance': None,
        },
        'data_type': {
            # 5mins for realtime
            'realtime': minutes(5),
            # Journey and customer satisfaction sets should update daily
            'journey': hours(25),
            'customer-satisfaction': hours(25),
            # Jobs run every hour, we're giving 2hrs as tolerance
            'monitoring': hours(2),
            # GCloud sales data is expected monthly
            'sales': months(1.25),
        }
    }
    for field in ['name', 'data_group', 'data_type']:
        try:
            max_ages = max_ages_for_field[field]
            return max_ages[bucket[field]]
        except KeyError:
            pass
    # Default to 1 month expectation
    return months(1)


def calculate_max_age_for(bucket, field, params):
    return params[bucket[field]]


def months(months):
    # Possibly not the most accurate comparison ever written.
    return months * hours(24) * 31


def hours(hours):
    return hours * (60 * 60)


def minutes(minutes):
    return minutes * 60

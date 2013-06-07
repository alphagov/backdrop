from backdrop.core import records
from backdrop.core.bucket import Bucket


def parse_and_store(db, incoming_data, bucket_name, logger):
    incoming_records = records.parse_all(incoming_data)

    logger.info(
        "request contains %s documents" % len(incoming_records))

    bucket = Bucket(db, bucket_name)
    bucket.store(incoming_records)

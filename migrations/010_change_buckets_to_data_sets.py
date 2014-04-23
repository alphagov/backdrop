"""
Change user buckets in users collection to data_sets
We have this as separate module to the migration
due to problems with naming python modules starting with digits
"""
from migrations.lib import change_buckets_to_data_sets


def up(db):
    change_buckets_to_data_sets.up(db)

from backdrop.core.bucket_new import Bucket
from hamcrest import assert_that, is_
from nose.tools import assert_raises


class TestBucket(object):
    def test_creating_a_bucket_with_raw_queries_allowed(self):
        bucket = Bucket("name", raw_queries_allowed=True)
        assert_that(bucket.raw_queries_allowed, is_(True))

    def test_bucket_name_validation(self):
        bucket_names = {
            "": False,
            "foo": True,
            "foo_bar": True,
            "12foo": False,
            123: False
        }
        for (bucket_name, name_is_valid) in bucket_names.items():
            if name_is_valid:
                Bucket(bucket_name)
            else:
                assert_raises(ValueError, Bucket, bucket_name)

import unittest
from hamcrest import assert_that
from backdrop.read import api
from tests.support.test_helpers import is_bad_request, is_ok


class TestRawEventAccess(unittest.TestCase):
    def setUp(self):
        api.app.config['RAW_QUERIES_ALLOWED']['foo'] = False
        self.app = api.app.test_client()

    def tearDown(self):
        api.app.config['RAW_QUERIES_ALLOWED']['foo'] = True

    def test_that_querying_for_raw_events_is_disabled(self):
        response = self.app.get("/foo?filter_by=foo:bar")
        assert_that(response, is_bad_request())

    def test_that_queries_with_group_by_are_allowed(self):
        response = self.app.get("/bar?filter_by=foo:bar&group_by=pie")
        assert_that(response, is_ok())

    def test_that_querying_for_less_than_7_days_periods_is_disabled(self):
        response = self.app.get(
            "/pub?"
            "group_by=guiness"
            "&start_at=2012-01-01T00:00:00Z"
            "&end_at=2012-01-07T23:59:30Z"
        )

        assert_that(response, is_bad_request())

    def test_that_querying_for_more_than_7_days_is_valid(self):
        response = self.app.get("/foo?group_by=pie"
                                "&start_at=2013-04-01T00:00:00Z"
                                "&end_at=2013-04-08T00:00:00Z")
        assert_that(response, is_ok())

    def test_that_non_midnight_values_are_disallowed_for_start_at(self):
        response = self.app.get("/foo?group_by=pie"
                                "&start_at=2012-01-01T00:01:00Z"
                                "&end_at=2012-01-09T00:00:00Z")

        assert_that(response, is_bad_request())

        response = self.app.get("/foo?group_by=pie"
                                "&start_at=2012-01-01T01:00:00Z"
                                "&end_at=2012-01-09T00:00:00Z")

        assert_that(response, is_bad_request())

        response = self.app.get("/foo?group_by=pie"
                                "&start_at=2012-01-01T01:01:00Z"
                                "&end_at=2012-01-09T00:00:00Z")

        assert_that(response, is_bad_request())

    def test_that_non_midnight_values_are_disallowed_for_end_at(self):
        response = self.app.get("/foo?group_by=pie"
                                "&end_at=2012-01-20T00:01:00Z"
                                "&start_at=2012-01-09T00:00:00Z")

        assert_that(response, is_bad_request())

        response = self.app.get("/foo?group_by=pie"
                                "&end_at=2012-01-20T01:00:00Z"
                                "&start_at=2012-01-09T00:00:00Z")

        assert_that(response, is_bad_request())

        response = self.app.get("/foo?group_by=pie"
                                "&end_at=2012-01-20T01:01:00Z"
                                "&start_at=2012-01-09T00:00:00Z")

        assert_that(response, is_bad_request())

    def test_on_invalid_dates(self):
        response = self.app.get("/foo?group_by=pie"
                                "&start_at=foo"
                                "&end_at=bar")

        assert_that(response, is_bad_request())

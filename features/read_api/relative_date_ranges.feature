@use_read_api_client
Feature: relative date queries for read api

    Scenario: querying for data when given one point and a positive delta
        Given "licensing_2.json" is in "foo" bucket
          and bucket setting raw_queries_allowed is true
         when I go to "/foo?date=2012-12-05T01:01:02%2B00:00&delta=1&period=week"
         then I should get back a status of "200"
          and the JSON should have "1" results
          and the "1st" result should be "{"_start_at": "2012-12-10T00:00:00+00:00", "_end_at": "2012-12-17T00:00:00+00:00", "_count": 4.0}"

    Scenario: querying for data when given one point and a negative delta
        Given "licensing_2.json" is in "foo" bucket
          and bucket setting raw_queries_allowed is true
         when I go to "/foo?date=2012-12-19T01:01:02%2B00:00&delta=-1&period=week"
         then I should get back a status of "200"
          and the JSON should have "1" results
          and the "1st" result should be "{"_start_at": "2012-12-10T00:00:00+00:00", "_end_at": "2012-12-17T00:00:00+00:00", "_count": 4.0}"


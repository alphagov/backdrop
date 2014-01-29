@use_read_api_client
Feature: relative date queries for read api

    Scenario: querying for periodic data from the start_at
        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?start_at=2012-12-12T00:00:00%2B00:00&duration=2&period=day"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should be "{"_start_at": "2012-12-12T00:00:00+00:00", "_end_at": "2012-12-13T00:00:00+00:00", "_count": 2.0}"
          and the "2nd" result should be "{"_start_at": "2012-12-13T00:00:00+00:00", "_end_at": "2012-12-14T00:00:00+00:00", "_count": 1.0}"

    Scenario: querying for periodic data from the end_at
        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?end_at=2012-12-14T00:00:00%2B00:00&duration=2&period=day"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should be "{"_start_at": "2012-12-12T00:00:00+00:00", "_end_at": "2012-12-13T00:00:00+00:00", "_count": 2.0}"
          and the "2nd" result should be "{"_start_at": "2012-12-13T00:00:00+00:00", "_end_at": "2012-12-14T00:00:00+00:00", "_count": 1.0}"

    Scenario: querying for periodic data from the start_at where the first results are empty
        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?start_at=2012-11-05T00:00:00%2B00:00&duration=10&period=week"
         then I should get back a status of "200"
          and the JSON should have "10" results
          and the "1st" result should be "{"_start_at": "2012-12-03T00:00:00+00:00", "_end_at": "2012-12-10T00:00:00+00:00", "_count": 1.0}"
          and the "2nd" result should be "{"_start_at": "2012-12-10T00:00:00+00:00", "_end_at": "2012-12-17T00:00:00+00:00", "_count": 4.0}"
          and the "3rd" result should be "{"_start_at": "2012-12-17T00:00:00+00:00", "_end_at": "2012-12-24T00:00:00+00:00", "_count": 0.0}"

    Scenario: querying for periodic data from the end_at where the first results are empty
        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?end_at=2013-02-04T00:00:00%2B00:00&duration=10&period=week"
         then I should get back a status of "200"
          and the JSON should have "10" results
          and the "10th" result should be "{"_start_at": "2012-12-10T00:00:00+00:00", "_end_at": "2012-12-17T00:00:00+00:00", "_count": 4.0}"
          and the "9th" result should be "{"_start_at": "2012-12-03T00:00:00+00:00", "_end_at": "2012-12-10T00:00:00+00:00", "_count": 1.0}"
          and the "8th" result should be "{"_start_at": "2012-11-26T00:00:00+00:00", "_end_at": "2012-12-03T00:00:00+00:00", "_count": 0.0}"


    Scenario: querying for grouped periodic data from the start_at
        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?start_at=2012-12-12T00:00:00%2B00:00&duration=2&period=day&group_by=authority"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should have "authority" equaling "Camden"
          and the "1st" result should have "values" with item "{"_start_at": "2012-12-12T00:00:00+00:00", "_end_at": "2012-12-13T00:00:00+00:00", "_count": 1.0}"
          and the "1st" result should have "values" with item "{"_start_at": "2012-12-13T00:00:00+00:00", "_end_at": "2012-12-14T00:00:00+00:00", "_count": 0.0}"
          and the "2nd" result should have "authority" equaling "Westminster"
          and the "2nd" result should have "values" with item "{"_start_at": "2012-12-12T00:00:00+00:00", "_end_at": "2012-12-13T00:00:00+00:00", "_count": 1.0}"
          and the "2nd" result should have "values" with item "{"_start_at": "2012-12-13T00:00:00+00:00", "_end_at": "2012-12-14T00:00:00+00:00", "_count": 1.0}"


    Scenario: querying for grouped periodic data from the end_at
        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?end_at=2012-12-14T00:00:00%2B00:00&duration=2&period=day&group_by=authority"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should have "authority" equaling "Camden"
          and the "1st" result should have "values" with item "{"_start_at": "2012-12-12T00:00:00+00:00", "_end_at": "2012-12-13T00:00:00+00:00", "_count": 1.0}"
          and the "1st" result should have "values" with item "{"_start_at": "2012-12-13T00:00:00+00:00", "_end_at": "2012-12-14T00:00:00+00:00", "_count": 0.0}"
          and the "2nd" result should have "authority" equaling "Westminster"
          and the "2nd" result should have "values" with item "{"_start_at": "2012-12-12T00:00:00+00:00", "_end_at": "2012-12-13T00:00:00+00:00", "_count": 1.0}"
          and the "2nd" result should have "values" with item "{"_start_at": "2012-12-13T00:00:00+00:00", "_end_at": "2012-12-14T00:00:00+00:00", "_count": 1.0}"


    Scenario: querying for grouped periodic data from the start_at where the first results are empty
        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?start_at=2012-12-10T00:00:00%2B00:00&duration=4&period=day&group_by=authority"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should have "authority" equaling "Camden"
          and the "1st" result should have "_count" equaling the integer "1"
          and the "2nd" result should have "authority" equaling "Westminster"
          and the "2nd" result should have "_count" equaling the integer "3"


    Scenario: querying for grouped periodic data from the end_at where the first results are empty
        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?end_at=2012-12-16T00:00:00%2B00:00&duration=2&period=day&group_by=authority"
         then I should get back a status of "200"
          and the JSON should have "1" results
          and the "1st" result should have "authority" equaling "Westminster"
          and the "1st" result should have "_count" equaling the integer "2"


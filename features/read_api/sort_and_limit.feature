@use_read_api_client
Feature: sorting and limiting

    Scenario: Sort the data on a key that has a numeric value in ascending order
        Given "sort_and_limit.json" is in "foo" bucket with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo?sort_by=value:ascending"
         then I should get back a status of "200"
          and the "1st" result should have "value" equaling the integer "3"
          and the "last" result should have "value" equaling the integer "8"

    Scenario: Sort the data on a key that has a numeric value in descending order
        Given "sort_and_limit.json" is in "foo" bucket with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo?sort_by=value:descending"
         then I should get back a status of "200"
          and the "1st" result should have "value" equaling the integer "8"
          and the "last" result should have "value" equaling the integer "3"

    Scenario: Limit the data to first 3 elements
        Given "sort_and_limit.json" is in "foo" bucket with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo?limit=3"
         then I should get back a status of "200"
          and the JSON should have "3" results

    Scenario: Sort grouped query on a key and limit
        Given "sort_and_limit.json" is in "foo" bucket
         when I go to "/foo?group_by=type&sort_by=_count:ascending&limit=1"
         then I should get back a status of "200"
          and the JSON should have "1" result
          and the "1st" result should have "type" equaling "domestic"

    Scenario: Sort periodic grouped query on a key
        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?group_by=authority&period=week&sort_by=_count:descending&start_at=2012-12-03T00:00:00Z&end_at=2012-12-17T00:00:00Z"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should have "authority" equaling "Westminster"

    Scenario: Limiting a periodic query is not allowed if start and end are defined
        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?period=week&limit=1&start_at=2012-12-03T00:00:00Z&end_at=2012-12-17T00:00:00Z"
         then I should get back a status of "400"


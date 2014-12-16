@use_read_api_client
Feature: inclusive end_at parameter

    @inclusive
    Scenario: not inclusive request
        Given "inclusive.json" is in "foo" data_set with settings
            | key                 | value |
            | data_group          | "foo" |
            | data_type           | "bar" |
            | raw_queries_allowed | true  |
         When I go to "/data/foo/bar?start_at=2014-12-01T00:00:00%2B00:00&end_at=2014-12-03T00:00:00%2B00:00"
         then I should get back a status of "200"
          and the JSON should have "2" results

    @inclusive
    Scenario: inclusive request
        Given "inclusive.json" is in "foo" data_set with settings
            | key                 | value |
            | data_group          | "foo" |
            | data_type           | "bar" |
            | raw_queries_allowed | true  |
         When I go to "/data/foo/bar?start_at=2014-12-01T00:00:00%2B00:00&end_at=2014-12-03T00:00:00%2B00:00&inclusive=true"
         then I should get back a status of "200"
          and the JSON should have "3" results

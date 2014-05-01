@use_http_client
Feature: querying for data grouped by day
    This feature is for querying for data grouped by day

    Scenario: grouping data by day between two timestamps
       Given I have the data in "daily_timestamps.json"
         And I have a data_set named "day" with settings
            | key        | value   |
            | data_group | "group" |
            | data_type  | "type"  |
           And I use the bearer token for the data_set
          When I POST to the specific path "/data/group/type"
          Then I should get back a status of "200"
          When I go to "/data/group/type?period=day&start_at=2013-04-04T00:00:00Z&end_at=2013-04-11T00:00:00Z"
          Then the JSON should have "7" results

@use_http_client
Feature: querying for data grouped by day
    This feature is for querying for data grouped by day

    @wip
    Scenario: grouping data by day
         Given I have the data in "daily_timestamps.json"
           And I have a bucket named "day"
          When I post the data to "/day"
          Then I should get back a status of "200"
          When I go to "/day?period=day"
          Then the JSON should have "12" results

    @wip
    Scenario: grouping data by day between two allowed timestamps
         Given I have the data in "daily_timestamps.json"
           And I have a bucket named "day"
          When I post the data to "/day"
          Then I should get back a status of "200"
          When I go to "/day?period=day&start_at=2013-04-04T00:00:00Z&end_at=2013-04-08T00:00:00Z"
          Then the JSON should have "4" results

    @wip
    Scenario: grouping data by day between two disallowed timestamps
         Given I have the data in "daily_timestamps.json"
           And I have a bucket named "day_no_raw_access"
          When I post the data to "/day_no_raw_access"
          Then I should get back a status of "200"
          When I go to "/day_no_raw_access?period=day&start_at=2013-05-02T00:00:00Z&end_at=2013-07-01T00:00:00Z"
          Then I should get back a status of "400"

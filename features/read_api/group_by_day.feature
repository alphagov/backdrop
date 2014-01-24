@use_http_client
Feature: querying for data grouped by day
    This feature is for querying for data grouped by day

    Scenario: grouping data by day between two timestamps
         Given I have the data in "daily_timestamps.json"
           And I have a bucket named "day"
          When I post the data to "/day"
          Then I should get back a status of "200"
          When I go to "/day?period=day&start_at=2013-04-04T00:00:00Z&end_at=2013-04-11T00:00:00Z"
          Then the JSON should have "7" results

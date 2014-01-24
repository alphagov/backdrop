@use_http_client
Feature: querying for data grouped by hour
    This feature is for querying for data grouped by hour

    Scenario: grouping data by hour between two days
         Given I have the data in "hourly_timestamps.json"
           And I have a bucket named "hour"
          When I post the data to "/hour"
          Then I should get back a status of "200"
          When I go to "/hour?period=hour&start_at=2013-04-01T13:00:00Z&end_at=2013-04-03T13:00:00Z"
          Then the JSON should have "48" results

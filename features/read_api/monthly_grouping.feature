@use_http_client
Feature: querying for data grouped by month
    This feature is for querying for data grouped by month

    Scenario: grouping data by month between two allowed timestamps
         Given I have the data in "monthly_timestamps.json"
           And I have a data_set named "month"
           And I use the bearer token for the data_set
          When I post the data to "/month"
          Then I should get back a status of "200"
          When I go to "/month?period=month&start_at=2013-05-01T00:00:00Z&end_at=2013-07-01T00:00:00Z"
          Then the JSON should have "2" results

    Scenario: grouping data by month between two disallowed timestamps
         Given I have the data in "monthly_timestamps.json"
           And I have a data_set named "month_with_wrong_timestamp"
           And I use the bearer token for the data_set
          When I post the data to "/month_with_wrong_timestamp"
          Then I should get back a status of "200"
          When I go to "/month_with_wrong_timestamp?period=month&start_at=2013-05-02T00:00:00Z&end_at=2013-07-01T00:00:00Z"
          Then I should get back a status of "400"

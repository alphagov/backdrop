@use_http_client
Feature: end-to-end platform test

    Scenario: write data to platform
        Given I have the data in "dinosaurs.json"
          and I have a data_set named "reptiles" with settings
            | key                 | value       |
            | raw_queries_allowed | true        |
            | data_group          | "reptiles"  |
            | data_type           | "fertility" |
          and I use the bearer token for the data_set
         when I POST to the specific path "/data/reptiles/fertility"
         then I should get back a status of "200"

    Scenario: write and retrieve data from platform
        Given I have the data in "dinosaurs.json"
          and I have a data_set named "reptiles" with settings
            | key                 | value       |
            | raw_queries_allowed | true        |
            | data_group          | "reptiles"  |
            | data_type           | "fertility" |
          and I use the bearer token for the data_set
         when I POST to the specific path "/data/reptiles/fertility"
          and I go to "/reptiles?filter_by=size:big"
         then I should get back a status of "200"
          and the JSON should have "2" result(s)

    Scenario: writing events and retrieving weekly data
        Given I have the data in "grouped_timestamps.json"
          and I have a data_set named "flavour_events" with settings
            | key                 | value       |
            | data_group          | "flavour"   |
            | data_type           | "events"    |
          and I use the bearer token for the data_set
         when I POST to the specific path "/data/flavour/events"
          and I go to "/flavour_events?period=week&group_by=flavour&start_at=2013-03-18T00:00:00Z&end_at=2013-04-08T00:00:00Z"
         then I should get back a status of "200"
          and the JSON should have "4" result(s)

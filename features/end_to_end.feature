@use_http_client
Feature: end-to-end platform test

    Scenario: write and retrieve data from platform
        Given I have the data in "dinosaurs.json"
         when I post the data to "/reptiles"
          and I go to "/reptiles?filter_by=size:big"
         then I should get back a status of "200"
          and the JSON should have "2" result(s)

    Scenario: writing events and retrieving weekly data
        Given I have the data in "grouped_timestamps.json"
         when I post the data to "/flavour_events"
          and I go to "/flavour_events?period=week&group_by=flavour"
         then I should get back a status of "200"
          and the JSON should have "3" result(s)

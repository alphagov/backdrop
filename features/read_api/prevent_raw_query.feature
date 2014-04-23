@use_read_api_client
Feature: preventing access to raw events

    Scenario: should prevent querying for raw events
        Given the api is running in protected mode
          And I have a data_set named "some_data_set"
         when I go to "/some_data_set?filter_by=name:foo"
         then I should get back a status of "400"

@use_read_api_client
Feature: preventing access to raw events

    Scenario: should prevent querying for raw events
        Given the api is running in protected mode
          And I have a bucket named "some_bucket"
         when I go to "/some_bucket?filter_by=name:foo"
         then I should get back a status of "400"

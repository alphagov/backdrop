@use_read_api_client
Feature: collect fields into grouped responses

    Scenario: should not be able to collect on non grouped queries
        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?collect=authority"
         then I should get back a status of "400"

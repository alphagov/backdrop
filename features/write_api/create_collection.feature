@use_write_api_client
Feature: create_collection

    Scenario: creating an uncapped collection
        Given I have JSON data '{"capped_size": 0}'
          and I have the bearer token "dev-create-endpoint-token"
         when I POST to the specific path "/data-sets/new-uncapped"
         then I should get back a status of "200"
          and the collection called "new-uncapped" should exist
          and the collection called "new-uncapped" should be uncapped

    Scenario: creating a capped collection
        Given I have JSON data '{"capped_size": 5040}'
          and I have the bearer token "dev-create-endpoint-token"
         when I POST to the specific path "/data-sets/new-capped"
         then I should get back a status of "200"
          and the collection called "new-capped" should exist
          and the collection called "new-capped" should be capped at "5040"

    Scenario: denying create collection with missing bearer token
        Given I have JSON data '{"capped_size": 0}'
         when I POST to the specific path "/data-sets/new-dataset"
         then I should get back a status of "401"
          and I should get a "WWW-Authenticate" header of "bearer"
          and I should get back the message "Unauthorized: invalid or no token given for "new-dataset"."

    Scenario: denying create collection with incorrect bearer token
        Given I have JSON data '{"capped_size": 0}'
          and I have the bearer token "invalid-bearer-token"
         when I POST to the specific path "/data-sets/new-dataset"
         then I should get back a status of "401"
          and I should get a "WWW-Authenticate" header of "bearer"
          and I should get back the message "Unauthorized: invalid or no token given for "new-dataset"."

    Scenario: not creating a collection if it already exists
        Given I have JSON data '{"capped_size": 4096}'
          and I have the bearer token "dev-create-endpoint-token"
         when I POST to the specific path "/data-sets/some-dataset"
          and I POST to the specific path "/data-sets/some-dataset"
         then I should get back a status of "400"

    Scenario: rejecting a missing capped_size when creating a collection
        Given I have JSON data '{}'
          and I have the bearer token "dev-create-endpoint-token"
          and I have a data_set named "new-dataset" with settings
            | key        | value       |
         when I POST to the specific path "/data-sets/new-dataset"
         then I should get back a status of "400"
          and the collection called "new-dataset" should not exist

    Scenario: rejecting an invalid capped_size when creating a collection
        Given I have JSON data '{"capped_size": "invalid"}'
          and I have the bearer token "dev-create-endpoint-token"
         when I POST to the specific path "/data-sets/new-dataset"
         then I should get back a status of "400"
          and the collection called "new-dataset" should not exist

    Scenario: rejecting an invalid JSON body when creating a collection
        Given I have JSON data '{broken}'
          and I have the bearer token "dev-create-endpoint-token"
         when I POST to the specific path "/data-sets/new-dataset"
         then I should get back a status of "400"
          and the collection called "new-dataset" should not exist

@use_write_api_client
Feature: the performance platform write api

    Scenario: hitting the health check url
         When I go to "/_status"
         then I should get back a status of "200"

    Scenario: posting to the health check URL
        Given I have the data in "dinosaur.json"
         when I POST to the specific path "/_status"
         then I should get back a status of "405"

    Scenario: posting to a reserved data_set name
        Given I have the data in "dinosaur.json"
         when I POST to the specific path "/_data_set"
         then I should get back a status of "404"

    Scenario: posting one object to a data_set
        Given I have the data in "dinosaur.json"
          and I have a data_set named "my_dinosaur_data_set" with settings
            | key        | value       |
            | data_group | "dinosaur"  |
            | data_type  | "droppings" |
          and I use the bearer token for the data_set
         when I POST to the specific path "/data/dinosaur/droppings"
         then I should get back a status of "200"
          and the stored data should contain "1" "name" equaling "t-rex"

    Scenario: posting a list of objects to a data_set
        Given I have the data in "dinosaurs.json"
          and I have a data_set named "my_dinosaur_data_set" with settings
            | key        | value       |
            | data_group | "dinosaur"  |
            | data_type  | "droppings" |
          and I use the bearer token for the data_set
         when I POST to the specific path "/data/dinosaur/droppings"
         then I should get back a status of "200"
          and the stored data should contain "2" "size" equaling "big"
          and the stored data should contain "1" "name" equaling "microraptor"

    Scenario: tagging data with week start at
        Given I have the data in "timestamps.json"
          and I have a data_set named "data_with_times" with settings
            | key        | value   |
            | data_group | "data"  |
            | data_type  | "times" |
          and I use the bearer token for the data_set
         when I POST to the specific path "/data/data/times"
         then I should get back a status of "200"
          and the stored data should contain "3" "_week_start_at" on "2013-03-11"
          and the stored data should contain "2" "_week_start_at" on "2013-03-18"

    Scenario: posting to a data_set with data group and data type
        Given I have the data in "timestamps.json"
          and I have a data_set named "data_with_times" with settings
            | key        | value         |
            | data_group | "transaction" |
            | data_type  | "timings"     |
          and I use the bearer token for the data_set
         when I POST to the specific path "/data/transaction/timings"
         then I should get back a status of "200"
          and the stored data should contain "3" "_week_start_at" on "2013-03-11"
          and the stored data should contain "2" "_week_start_at" on "2013-03-18"

    Scenario: unauthorized when posting with an incorrect token
        Given I have JSON data '[]'
          and I have a data_set named "some_data_set" with settings
            | key        | value   |
            | data_group | "group" |
            | data_type  | "type"  |
          and I have the bearer token "invalid-bearer-token"
         when I POST to the specific path "/data/group/type"
         then I should get back a status of "401"
          and I should get a "WWW-Authenticate" header of "bearer"
          and I should get back the message "Unauthorized: Invalid bearer token "invalid-bearer-token""

    Scenario: denying create collection with missing bearer token
        Given I have JSON data '{"capped_size": 0}'
         when I POST to the specific path "/data-sets/new-dataset"
         then I should get back a status of "401"
          and I should get a "WWW-Authenticate" header of "bearer"
          and I should get back the message "Unauthorized: invalid or no token given."

    Scenario: denying create collection with incorrect bearer token
        Given I have JSON data '{"capped_size": 0}'
          and I have the bearer token "invalid-bearer-token"
         when I POST to the specific path "/data-sets/new-dataset"
         then I should get back a status of "401"
          and I should get a "WWW-Authenticate" header of "bearer"
          and I should get back the message "Unauthorized: invalid or no token given."

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

    @delete_things
    Scenario: deleting a data-set
        Given I have a data_set named "some-dataset" with settings
            | key        | value       |
          and I have JSON data '{"capped_size": 4096}'
          and I have the bearer token "dev-create-endpoint-token"
         when I POST to the specific path "/data-sets/some-dataset"
         then the collection called "some-dataset" should exist
         when I send a DELETE request to "/data-sets/some-dataset"
         then I should get back a status of "200"
          and I should get back the message "Deleted some-dataset"
          and the collection called "some-dataset" should not exist

    @delete_things
    Scenario: trying to delete a data-set that does not exist
        Given I have the bearer token "dev-create-endpoint-token"
         when I send a DELETE request to "/data-sets/some-dataset"
         then I should get back a status of "404"
          and I should get back the message "No collection exists with name "some-dataset""

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

    Scenario: rejecting an JSON body when creating a collection
        Given I have JSON data '{broken}'
          and I have the bearer token "dev-create-endpoint-token"
         when I POST to the specific path "/data-sets/new-dataset"
         then I should get back a status of "400"
          and the collection called "new-dataset" should not exist

    @empty_data_set
    Scenario: emptying a data-set by PUTing an empty JSON list
        Given I have the data in "dinosaur.json"
          and I have a data_set named "some_data_set" with settings
            | key        | value         |
            | data_group | "group"       |
            | data_type  | "type"        |
          and I use the bearer token for the data_set
         when I POST to the specific path "/data/group/type"
        given I have JSON data '[]'
         when I PUT to the specific path "/data/group/type"
         then I should get back a status of "200"
          and the collection called "some_data_set" should exist
          and the collection called "some_data_set" should contain 0 records
          and I should get back the message "some_data_set now contains 0 records"

    @empty_data_set
    Scenario: PUT is only implemented for an empty JSON list
        Given I have a data_set named "some_data_set" with settings
            | key        | value         |
            | data_group | "group"       |
            | data_type  | "type"        |
          and I use the bearer token for the data_set
        given I have JSON data '[{"a": 1}]'
         when I PUT to the specific path "/data/group/type"
         then I should get back a status of "400"
          and I should get back the message "Not implemented: you can only pass an empty JSON list"

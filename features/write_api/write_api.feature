@use_write_api_client
Feature: the performance platform write api

    Scenario: hitting the health check url
         When I go to "/_status"
         then I should get back a status of "200"

    Scenario: posting to the health check URL
        Given I have the data in "dinosaur.json"
         when I post the data to "/_status"
         then I should get back a status of "405"

    Scenario: posting to a reserved data_set name
        Given I have the data in "dinosaur.json"
         when I post the data to "/_data_set"
         then I should get back a status of "404"

    Scenario: posting one object to a data_set
        Given I have the data in "dinosaur.json"
          and I have a data_set named "my_dinosaur_data_set"
          and I use the bearer token for the data_set
         when I post the data to "/my_dinosaur_data_set"
         then I should get back a status of "200"
          and the stored data should contain "1" "name" equaling "t-rex"

    Scenario: posting a list of objects to a data_set
        Given I have the data in "dinosaurs.json"
          and I have a data_set named "my_dinosaur_data_set"
          and I use the bearer token for the data_set
         when I post the data to "/my_dinosaur_data_set"
         then I should get back a status of "200"
          and the stored data should contain "2" "size" equaling "big"
          and the stored data should contain "1" "name" equaling "microraptor"

    Scenario: tagging data with week start at
        Given I have the data in "timestamps.json"
          and I have a data_set named "data_with_times"
          and I use the bearer token for the data_set
         when I post the data to "/data_with_times"
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
         when I post to the specific path "/data/transaction/timings"
         then I should get back a status of "200"
          and the stored data should contain "3" "_week_start_at" on "2013-03-11"
          and the stored data should contain "2" "_week_start_at" on "2013-03-18"

    Scenario: denying create collection with missing bearer token
        Given I have JSON data '{"capped_size": 0}'
         when I post the data to "/data-sets/new-dataset"
         then I should get back a status of "403"

    Scenario: denying create collection with incorrect bearer token
        Given I have JSON data '{"capped_size": 0}'
          and I have the bearer token "invalid-bearer-token"
         when I post the data to "/data-sets/new-dataset"
         then I should get back a status of "403"

    Scenario: creating an uncapped collection
        Given I have JSON data '{"capped_size": 0}'
          and I have the bearer token "dev-create-endpoint-token"
         when I post the data to "/data-sets/new-uncapped"
         then I should get back a status of "200"
          and the collection called "new-uncapped" should exist
          and the collection called "new-uncapped" should be uncapped

    Scenario: creating a capped collection
        Given I have JSON data '{"capped_size": 5040}'
          and I have the bearer token "dev-create-endpoint-token"
         when I post the data to "/data-sets/new-capped"
         then I should get back a status of "200"
          and the collection called "new-capped" should exist
          and the collection called "new-capped" should be capped at "5040"

    @delete_things
    Scenario: deleting a data-set
	Given I have a data_set named "my-data-set"
          and I have the bearer token "fake stagecraft token"
	 when I send a delete request to "/data-sets/my-data-set"
         then I should get back a status of "200"
	  and the collection called "my-data-set" should not exist

    Scenario: not creating a collection if it already exists
        Given I have JSON data '{"capped_size": 4096}'
          and I have the bearer token "dev-create-endpoint-token"
         when I post the data to "/data-sets/some-dataset"
          and I post the data to "/data-sets/some-dataset"
         then I should get back a status of "400"

    Scenario: rejecting a missing capped_size when creating a collection
        Given I have JSON data '{}'
          and I have the bearer token "dev-create-endpoint-token"
          and I have a data_set named "new-dataset"
         when I post the data to "/data-sets/new-dataset"
         then I should get back a status of "400"
          and the collection called "new-dataset" should not exist

    Scenario: rejecting an invalid capped_size when creating a collection
        Given I have JSON data '{"capped_size": "invalid"}'
          and I have the bearer token "dev-create-endpoint-token"
         when I post the data to "/data-sets/new-dataset"
         then I should get back a status of "400"
          and the collection called "new-dataset" should not exist

    Scenario: rejecting an JSON body when creating a collection
        Given I have JSON data '{broken}'
          and I have the bearer token "dev-create-endpoint-token"
         when I post the data to "/data-sets/new-dataset"
         then I should get back a status of "400"
          and the collection called "new-dataset" should not exist

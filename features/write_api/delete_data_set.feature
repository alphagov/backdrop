@use_write_api_client
Feature: delete_data_set

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
    Scenario: cannot delete a data-set that does not exist
        Given I have the bearer token "dev-create-endpoint-token"
         when I send a DELETE request to "/data-sets/some-dataset"
         then I should get back a status of "404"
          and I should get back the message "No collection exists with name "some-dataset""

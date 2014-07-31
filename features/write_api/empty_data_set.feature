@use_write_api_client
Feature: empty_data_set

    @empty_data_set
    Scenario: emptying a data-set by PUTing an empty JSON list
        Given I have the data in "dinosaur.json"
          and I have a data_set named "some_data_set" with settings
            | key         | value         |
            | data_group  | "group"       |
            | data_type   | "type"        |
            | capped_size | 0             |
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
            | key         | value         |
            | data_group  | "group"       |
            | data_type   | "type"        |
            | capped_size | 0             |
          and I use the bearer token for the data_set
        given I have JSON data '[{"a": 1}]'
         when I PUT to the specific path "/data/group/type"
         then I should get back a status of "400"
          and I should get back the message "Not implemented: you can only pass an empty JSON list"

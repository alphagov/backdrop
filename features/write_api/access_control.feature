@use_write_api_client
Feature: access_control
    @posting_things
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
          and I should get back the message "Unauthorized: Invalid bearer token "invalid-bearer-token" for "some_data_set""

    @posting_things
    Scenario: unauthorized when posting with a badly formed authorization header
      Given I have JSON data '[]'
        and I have a data_set named "some_data_set" with settings
          | key        | value   |
          | data_group | "group" |
          | data_type  | "type"  |
        and I use the bearer token for the data_set
       when I POST to "/data/group/type" with a malformed authorization header
       then I should get back a status of "401"
        and I should get a "WWW-Authenticate" header of "bearer"
        and I should get back the message "Expected header of form: Authorization: Bearer <token>"

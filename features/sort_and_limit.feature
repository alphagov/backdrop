@use_read_api_client
Feature: sorting and limiting

    Scenario: Sort the data on a key that has a numeric value in ascending order
        Given "sort_and_limit.json" is in "foo" bucket
         when I go to "/foo?sort_by=value:ascending"
         then I should get back a status of "200"
          and the "1st" result should have "value" equaling the integer "3"
          and the "last" result should have "value" equaling the integer "8"

    Scenario: Sort the data on a key that has a numeric value in descending order
        Given "sort_and_limit.json" is in "foo" bucket
         when I go to "/foo?sort_by=value:descending"
         then I should get back a status of "200"
          and the "1st" result should have "value" equaling the integer "8"
          and the "last" result should have "value" equaling the integer "3"

    Scenario: Limit the data to first 3 elements
        Given "sort_and_limit.json" is in "foo" bucket
         when I go to "/foo?limit=3"
         then I should get back a status of "200"
          and the JSON should have "3" results




    Scenario: Sort grouped query on a key and limit
        Given "sort_and_limit.json" is in "foo" bucket
         when I go to "/foo?group_by=type&sort_by=_count:ascending&limit=1"
         then I should get back a status of "200"
          and the JSON should have "1" result
          and the "1st" result should have "type" equaling "domestic"

# Scenario: Group and Sort the data on a key that has a numeric value in ascending order  
         
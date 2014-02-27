@use_read_api_client
Feature: the performance platform read api

    Scenario: getting all the data in a bucket
        Given "licensing.json" is in "foo" bucket with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo"
         then I should get back a status of "200"
          and the JSON should have "6" results

    Scenario: my data does not have timestamps
        Given "dinosaurs.json" is in "rawr" bucket with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/rawr"
         then I should get back a status of "200"
         and the JSON should have "4" results

    Scenario: querying a bucket that does not exist
        Given Stagecraft is running
         when I go to "/foobar"
         then I should get back a status of "404"

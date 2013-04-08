@use_read_api_client
Feature: the performance platform read api

    Scenario: getting all the data in a bucket
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo"
         then I should get back a status of "200"
          and the JSON should have "6" results

    Scenario: my data does not have timestamps
        Given "dinosaurs.json" is in "rawr" bucket
         when I go to "/rawr"
         then I should get back a status of "200"
         and the JSON should have "4" results


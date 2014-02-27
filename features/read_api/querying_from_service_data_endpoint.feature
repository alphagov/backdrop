@use_read_api_client
Feature: Querying data from service-data endpoint

    Scenario: querying data
        Given "dinosaurs.json" is in "rawr" bucket with settings
            | key                 | value       |
            | data_group          | "dinosaurs" |
            | data_type           | "taxonomy"  |
            | raw_queries_allowed | true        |
         when I go to "/data/dinosaurs/taxonomy?filter_by=eats_people:true"
         then I should get back a status of "200"
          and the JSON should have "3" results

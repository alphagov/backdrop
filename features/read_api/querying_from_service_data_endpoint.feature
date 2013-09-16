@use_read_api_client
Feature: Querying data from service-data endpoint

    Scenario: querying data
        Given "dinosaurs.json" is in "rawr" bucket
          and bucket setting service is "dinosaurs"
          and bucket setting data_type is "taxonomy"
          and bucket setting raw_queries_allowed is true
         when I go to "/service-data/dinosaurs/taxonomy?filter_by=eats_people:true"
         then I should get back a status of "200"
          and the JSON should have "3" results
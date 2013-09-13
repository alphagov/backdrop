@use_read_api_client
Feature: Querying data from service-data endpoint

    @wip
    Scenario: querying data
        Given I have a bucket named "rawr"
          and bucket setting service is "dinosaurs"
          and bucket setting data_type is "taxonomy"
          and "dinosaurs.json" is in "rawr" bucket
         when I go to "/service-data/dinosaurs/taxonomy"
         then I should get back a status of "200"
          and the JSON should have "4" results
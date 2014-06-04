@use_read_api_client
@in_work
Feature: published status in responses

    Scenario: querying a data_set that is published
        Given I have a data_set named "published_data_set" with settings
            | key                 | value |
            | published           | true  |
            | raw_queries_allowed | true  |
         when I go to "/published_data_set"
         then I should get back a status of "200"

    Scenario: querying a data_set that is unpublished
        Given I have a data_set named "unpublished_data_set" with settings
            | key                 | value |
            | published           | false |
            | raw_queries_allowed | true  |
         when I go to "/unpublished_data_set"
         then I should get back a status of "200"
          and I should get back a warning of "Warning: This data-set is unpublished. Data may be subject to change or be inaccurate."

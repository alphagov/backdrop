@use_read_api_client
Feature: the read/status api

    Scenario: checking an in-date data_set
        Given I have a data_set named "recent" with settings
            | key              | value |
            | max_age_expected | 60    |
        and I have a record updated "10 seconds" ago in the "recent" data_set
        when I go to "/_status/data-sets"
        then I should get back a status of "200"

    Scenario: checking an out-of-date data_set
        Given I have a data_set named "recent" with settings
            | key              | value |
            | max_age_expected | 1     |
        and I have a record updated "10 seconds" ago in the "recent" data_set
        when I go to "/_status/data-sets"
        then I should get back a status of "500"

    Scenario: checking a data_set with no max age expected
        Given I have a data_set named "recent" with settings
            | key              | value |
            | max_age_expected | None  |
        and I have a record updated "10 seconds" ago in the "recent" data_set
        when I go to "/_status/data-sets"
        then I should get back a status of "200"

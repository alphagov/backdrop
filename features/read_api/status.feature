@use_read_api_client
Feature: the read/status api

    Scenario: checking an in-date bucket
        Given I have a bucket named "recent" with settings
            | key              | value |
            | max_age_expected | 60    |
        and I have a record updated "10 seconds" ago in the "recent" bucket
        when I go to "/_status/buckets"
        then I should get back a status of "200"

    Scenario: checking an out-of-date bucket
        Given I have a bucket named "recent" with settings
            | key              | value |
            | max_age_expected | 1     |
        and I have a record updated "10 seconds" ago in the "recent" bucket
        when I go to "/_status/buckets"
        then I should get back a status of "500"

    Scenario: checking a bucket with no max age expected
        Given I have a bucket named "recent" with settings
            | key              | value |
            | max_age_expected | None  |
        and I have a record updated "10 seconds" ago in the "recent" bucket
        when I go to "/_status/buckets"
        then I should get back a status of "200"

@use_read_api_client
Feature: the read/status api

    Scenario: checking an in-date bucket
        Given I have a record updated "10 seconds" ago in the "recent" bucket
        and bucket setting max_age_expected is 60
        when I go to "/_status/buckets"
        then I should get back a status of "200"

    Scenario: checking an out-of-date bucket
        Given I have a record updated "10 seconds" ago in the "recent" bucket
        and bucket setting max_age_expected is 1
        when I go to "/_status/buckets"
        then I should get back a status of "500"

    Scenario: checking a bucket with no max age expected
        Given I have a record updated "10 seconds" ago in the "recent" bucket
        and bucket setting max_age_expected is None
        when I go to "/_status/buckets"
        then I should get back a status of "200"

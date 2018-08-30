@use_http_client
Feature: the read api should provide cache control headers
    Scenario: _status is not cacheable
         when I go to "/_status"
         then the "Cache-Control" header should be "no-cache"

    Scenario: query returns an etag
        Given "licensing.json" is in "foo" data_set with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo"
         then the "ETag" header should not be empty

    Scenario: response is Not Modified when etag matches
        Given "licensing.json" is in "foo" data_set
         when I go to "/foo"
          and I send another request to "/foo" with the received etag
         then I should get back a status of "304"

    Scenario: non-realtime data sets have a 30 minute cache header
        Given "licensing.json" is in "foo" data_set with settings
            | key                 | value |
            | raw_queries_allowed | true  |
            | realtime            | false |
            | published           | true  |
         when I go to "/foo"
         then the "Cache-Control" header should be "max-age=1800, must-revalidate"

    Scenario: realtime data sets have a 2 minute cache header
        Given "licensing.json" is in "foo" data_set with settings
            | key                 | value |
            | raw_queries_allowed | true  |
            | realtime            | true  |
            | published           | true  |
         when I go to "/foo"
         then the "Cache-Control" header should be "max-age=120, must-revalidate"

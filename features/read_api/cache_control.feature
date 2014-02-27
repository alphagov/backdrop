@use_http_client
Feature: the read api should provide cache control headers
    Scenario: _status is not cacheable
         when I go to "/_status"
         then the "Cache-Control" header should be "no-cache"

    Scenario: query returns an etag
        Given "licensing.json" is in "foo" bucket with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo"
         then the "ETag" header should be ""7c7cec78f75fa9f30428778f2b6da9b42bd104d0""

    Scenario: response is Not Modified when etag matches
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo"
          and I send another request to "/foo" with the received etag
         then I should get back a status of "304"

@use_http_client
Feature: the read api should provide cache control headers
    Scenario: _status is not cacheable
         when I go to "/_status"
         then the "Cache-Control" header should be "no-cache"

    Scenario: query is cached for 1 hour
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo"
         then the "Cache-Control" header should be "max-age=3600, must-revalidate"

    Scenario: query returns an etag
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo"
         then the "ETag" header should be ""f739cff7a1ba212cff7e8003ac193d0bf9101551""

    Scenario: response is Not Modified when etag matches
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo"
          and I send another request to "/foo" with the received etag
         then I should get back a status of "304"
@use_read_api_client
Feature: filtering queries for read api

    Scenario: querying for data ON or AFTER a certain point
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo?start_at=2012-12-13T01:01:01%2B00:00"
         then I should get back a status of "400"

    Scenario: querying for data BEFORE a certain point
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo?end_at=2012-12-12T01:01:02%2B00:00"
         then I should get back a status of "400"

    Scenario: querying for data between two points
        Given "licensing.json" is in "foo" bucket with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo?start_at=2012-12-12T01:01:02%2B00:00&end_at=2012-12-14T00:00:00%2B00:00"
         then I should get back a status of "200"
          and the JSON should have "1" results
          and the "1st" result should be "{"_timestamp": "2012-12-13T01:01:01+00:00", "licence_name": "Temporary events notice", "interaction": "success", "authority": "Westminster", "type": "success", "_id": "1236"}"


    Scenario: filtering by a key and value
        Given "licensing.json" is in "foo" bucket with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo?filter_by=authority:Camden"
         then I should get back a status of "200"
          and the JSON should have "2" results

    Scenario: invalid start_at parameter
        Given I have a bucket named "foo"
         When I go to "/foo?start_at=not+a+date"
         then I should get back a status of "400"

    Scenario: filtering by a field name starting with "$" is not allowed because of security reasons
        Given "licensing.json" is in "weekly" bucket
         when I go to "/weekly?filter_by=$where:function(){}"
         then I should get back a status of "400"


    Scenario: querying for data between two points and filtered by a key and value
        Given "licensing.json" is in "foo" bucket with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo?start_at=2012-12-13T00:00:02%2B00:00&end_at=2012-12-19T00:00:00%2B00:00&filter_by=type:success"
         then I should get back a status of "200"
          and the JSON should have "1" results
          and the "1st" result should be "{"_timestamp": "2012-12-13T01:01:01+00:00", "licence_name": "Temporary events notice", "interaction": "success", "authority": "Westminster", "type": "success", "_id": "1236"}"

    Scenario: querying for boolean kind of data
        Given "dinosaurs.json" is in "lizards" bucket with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/lizards?filter_by=eats_people:true"
         then I should get back a status of "200"
          and the JSON should have "3" results

    Scenario: querying for more boolean data
        Given "dinosaurs.json" is in "lizards" bucket
         when I go to "/lizards?group_by=eats_people"
         then I should get back a status of "200"
         and the JSON should have "2" results

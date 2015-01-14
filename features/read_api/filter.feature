@use_read_api_client
Feature: filtering queries for read api

    Scenario: querying for data ON or AFTER a certain point
        Given "licensing.json" is in "foo" data_set
         when I go to "/foo?start_at=2012-12-13T01:01:01%2B00:00"
         then I should get back a status of "400"

    Scenario: querying for data BEFORE a certain point
        Given "licensing.json" is in "foo" data_set
         when I go to "/foo?end_at=2012-12-12T01:01:02%2B00:00"
         then I should get back a status of "400"

    Scenario: querying for data between two points
        Given "licensing.json" is in "foo" data_set with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo?start_at=2012-12-12T01:01:02%2B00:00&end_at=2012-12-14T00:00:00%2B00:00"
         then I should get back a status of "200"
          and the JSON should have "1" results
          and the "1st" result should be "{"_timestamp": "2012-12-13T01:01:01+00:00", "licence_name": "Temporary events notice", "interaction": "success", "authority": "Westminster", "type": "success", "_id": "1236"}"


    Scenario: filtering by a key and value
        Given "licensing.json" is in "foo" data_set with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo?filter_by=authority:Camden"
         then I should get back a status of "200"
          and the JSON should have "2" results

    Scenario: invalid start_at parameter
        Given I have a data_set named "foo" with settings
            | key        | value   |
            | data_group | "group" |
            | data_type  | "type"  |
         When I go to "/data/group/type?start_at=not+a+date"
         then I should get back a status of "400"

    Scenario: filtering by a field name starting with "$" is not allowed because of security reasons
        Given "licensing.json" is in "weekly" data_set
         when I go to "/weekly?filter_by=$where:function(){}"
         then I should get back a status of "400"


    Scenario: querying for data between two points and filtered by a key and value
        Given "licensing.json" is in "foo" data_set with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo?start_at=2012-12-13T00:00:02%2B00:00&end_at=2012-12-19T00:00:00%2B00:00&filter_by=type:success"
         then I should get back a status of "200"
          and the JSON should have "1" results
          and the "1st" result should be "{"_timestamp": "2012-12-13T01:01:01+00:00", "licence_name": "Temporary events notice", "interaction": "success", "authority": "Westminster", "type": "success", "_id": "1236"}"

    Scenario: querying for boolean kind of data
        Given "dinosaurs.json" is in "lizards" data_set with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/lizards?filter_by=eats_people:true"
         then I should get back a status of "200"
          and the JSON should have "3" results

    Scenario: filtering by a key and prefix value
        Given "licensing.json" is in "foo" data_set with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo?filter_by_prefix=authority:Camd"
         then I should get back a status of "200"
          and the JSON should have "2" results

    Scenario: prefix filtering by a field name starting with "$" is not allowed because of security reasons
        Given "licensing.json" is in "weekly" data_set
         when I go to "/weekly?filter_by_prefix=$prefix:function(){}"
         then I should get back a status of "400"

    Scenario: prefix filtering does not execute regex search
        Given "licensing.json" is in "foo" data_set with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo?filter_by_prefix=authority:.*"
         then I should get back a status of "200"
          and the JSON should have "0" results

    Scenario: querying for data between two points and filtered by a key and prefix value
        Given "licensing.json" is in "foo" data_set with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/foo?start_at=2012-12-13T00:00:02%2B00:00&end_at=2012-12-19T00:00:00%2B00:00&filter_by_prefix=type:succ"
         then I should get back a status of "200"
          and the JSON should have "1" results
          and the "1st" result should be "{"_timestamp": "2012-12-13T01:01:01+00:00", "licence_name": "Temporary events notice", "interaction": "success", "authority": "Westminster", "type": "success", "_id": "1236"}"

    Scenario: query does not convert to boolean with prefix filter
        Given "dinosaurs.json" is in "lizards" data_set with settings
            | key                 | value |
            | raw_queries_allowed | true  |
         when I go to "/lizards?filter_by_prefix=eats_people:true"
         then I should get back a status of "200"
          and the JSON should have "0" results

    Scenario: querying for more boolean data
        Given "dinosaurs.json" is in "lizards" data_set
         when I go to "/lizards?group_by=eats_people"
         then I should get back a status of "200"
         and the JSON should have "2" results

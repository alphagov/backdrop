@use_read_api_client
Feature: the performance platform read api

    Scenario: getting all the data in a bucket
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo"
         then I should get back a status of "200"
          and the JSON should have "6" results

    Scenario: my data does not have timestamps
        Given "dinosaurs.json" is in "rawr" bucket
         when I go to "/rawr"
         then I should get back a status of "200"
         and the JSON should have "4" results

    Scenario: querying for data ON or AFTER a certain point
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo?start_at=2012-12-13T01:01:01%2B00:00"
         then I should get back a status of "200"
          and the JSON should have "4" results
          and the "1st" result should be "{"_timestamp": "2012-12-13T01:01:01+00:00", "authority": "Westminster", "interaction": "success", "licence_name": "Temporary events notice", "_id": "1236", "type": "success"}"

    Scenario: querying for data BEFORE a certain point
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo?end_at=2012-12-12T01:01:02%2B00:00"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should be "{"_timestamp": "2012-12-12T01:01:01+00:00", "licence_name": "Temporary events notice", "interaction": "success", "authority": "Westminster", "type": "success", "_id": "1234"}"

    Scenario: querying for data between two points
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo?start_at=2012-12-12T01:01:02%2B00:00&end_at=2012-12-14T00:00:00%2B00:00"
         then I should get back a status of "200"
          and the JSON should have "1" results
          and the "1st" result should be "{"_timestamp": "2012-12-13T01:01:01+00:00", "licence_name": "Temporary events notice", "interaction": "success", "authority": "Westminster", "type": "success", "_id": "1236"}"


    Scenario: filtering by a key and value
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo?filter_by=authority:Camden"
         then I should get back a status of "200"
          and the JSON should have "2" results

    Scenario: grouping data by a key
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo?group_by=authority"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should be "{"Westminster": 4}"
          and the "2nd" result should be "{"Camden": 2}"

    Scenario: extracting data for a representation
        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?group_by=authority&filter_by=licence_name:Temporary%20events%20notice"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should be "{"Westminster": 3}"

        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?group_by=licence_name&filter_by=authority:Westminster"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should be "{"Temporary events notice": 3}"
          and the "2nd" result should be "{"Cat herding licence": 1}"

    Scenario: invalid request parameters
         When I go to "/foo?start_at=not+a+date"
         then I should get back a status of "400"

    Scenario: grouping data by time period - week
        Given "stored_timestamps.json" is in "weekly" bucket
         when I go to "/weekly?period=week"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should be "{"_count": 3.0, "_start_at": "2013-03-11T00:00:00+00:00", "_end_at" : "2013-03-18T00:00:00+00:00"}"
          and the "2nd" result should be "{"_count": 2.0, "_start_at": "2013-03-18T00:00:00+00:00", "_end_at" : "2013-03-25T00:00:00+00:00"}"

    Scenario: grouping data by time period (week) and filtering
        Given "stored_timestamps_for_filtering.json" is in "weekly" bucket
         when I go to "/weekly?period=week&filter_by=name:alpha"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should be "{"_count": 2.0, "_start_at": "2013-03-11T00:00:00+00:00", "_end_at" : "2013-03-18T00:00:00+00:00"}"
          and the "2nd" result should be "{"_count": 1.0, "_start_at": "2013-03-18T00:00:00+00:00", "_end_at" : "2013-03-25T00:00:00+00:00"}"

    Scenario: grouping data by time period (week) and a name
        Given "stored_timestamps_for_filtering.json" is in "weekly" bucket
         when I go to "/weekly?period=week&group_by=name"
         then I should get back a status of "200"
         and the JSON should have "2" results
         and the "1st" result should be "{"_count": 3.0, "_group_count": 2.0, "_start_at": "2013-03-11T00:00:00+00:00", "_end_at" : "2013-03-18T00:00:00+00:00", "name": { "alpha": { "_count" : 2.0 }, "beta": { "_count" : 1.0 } } }"

    Scenario: grouping data by time period (week) and a name that doesn't exist
        Given "stored_timestamps_for_filtering.json" is in "weekly" bucket
         when I go to "/weekly?period=week&group_by=wibble"
         then I should get back a status of "200"
         and the JSON should have "0" results

    Scenario: grouping data by a period and field representing period is invalid
        Given "licensing.json" is in "weekly" bucket
         when I go to "/weekly?period=week&group_by=_week_start_at"
         then I should get back a status of "400"
          and I should get back a message: "{ "status": "error", "message": "Cannot group on two equal keys" }"

    Scenario: grouping data by internal fields is not allowed
        Given "licensing.json" is in "weekly" bucket
         when I go to "/weekly?group_by=_anything"
         then I should get back a status of "400"
          and I should get back a message: "{ "status": "error", "message": "Cannot group by internal fields" }"

    Scenario: filtering by a field name starting with "$" is not allowed because of security reasons
        Given "licensing.json" is in "weekly" bucket
         when I go to "/weekly?filter_by=$where:function(){}"
         then I should get back a status of "400"
          and I should get back a message: "{ "status": "error", "message": "filter_by is not valid" }"

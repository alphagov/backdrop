@use_read_api_client
Feature: grouping queries for read api
    This feature is about all types of grouped query (group_by and period). It
    includes filtering on these types of query.

    Scenario: grouping data by a key
        Given "licensing.json" is in "foo" bucket
         when I go to "/foo?group_by=authority"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should be "{"authority": "Westminster", "_count": 4}"
          and the "2nd" result should be "{"authority": "Camden", "_count": 2}"

    Scenario: grouping and filtering by different keys
        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?group_by=authority&filter_by=licence_name:Temporary%20events%20notice"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should be "{"authority": "Westminster", "_count": 3}"

        Given "licensing_2.json" is in "foo" bucket
         when I go to "/foo?group_by=licence_name&filter_by=authority:Westminster"
         then I should get back a status of "200"
          and the JSON should have "2" results
          and the "1st" result should be "{"licence_name": "Temporary events notice", "_count": 3}"
          and the "2nd" result should be "{"licence_name": "Cat herding licence", "_count": 1}"


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
           and the "1st" result should have "values" with item "{"_start_at": "2013-03-11T00:00:00+00:00", "_end_at": "2013-03-18T00:00:00+00:00", "_count": 2.0}"


    Scenario: grouping data by time period (week) and a name and filtered by a key and value
        Given "stored_timestamps_for_filtering.json" is in "weekly" bucket
         when I go to "/weekly?period=week&group_by=name&filter_by=name:alpha"
         then I should get back a status of "200"
           and the JSON should have "1" results
           and the "1st" result should have "values" with item "{"_start_at": "2013-03-11T00:00:00+00:00", "_end_at": "2013-03-18T00:00:00+00:00", "_count": 2.0}"
           and the "1st" result should have "values" with item "{"_start_at": "2013-03-18T00:00:00+00:00", "_end_at": "2013-03-25T00:00:00+00:00", "_count": 1.0}"


    Scenario: grouping data by time period (week) and a name that doesn't exist
        Given "stored_timestamps_for_filtering.json" is in "weekly" bucket
         when I go to "/weekly?period=week&group_by=wibble"
         then I should get back a status of "200"
          and the JSON should have "0" results


    Scenario: grouping data by a period and field representing period is invalid
        Given "licensing.json" is in "weekly" bucket
         when I go to "/weekly?period=week&group_by=_week_start_at"
         then I should get back a status of "400"

    Scenario: grouping data by internal fields is not allowed
        Given "licensing.json" is in "weekly" bucket
         when I go to "/weekly?group_by=_anything"
         then I should get back a status of "400"

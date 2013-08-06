@use_read_api_client
Feature: more complex combination of parameters that are used by clients


    Background:
          Given "licensing_preview.json" is in "licensing" bucket


    Scenario: for an authority get weekly data for the top 3 licences between two points in time
         when I go to "/licensing?group_by=licenceUrlSlug&filter_by=authorityUrlSlug:testport&start_at=2013-01-28T00:00:00%2B00:00&end_at=2013-03-29T00:00:00%2B00:00&period=week&collect=authorityName&collect=licenceName&sort_by=_count:descending&limit=3"
         then I should get back a status of "200"
          and the JSON should have "3" results
          and the "1st" result should have "licenceUrlSlug" equaling "fake-licence-3"
          and the "1st" result should have "values" with item "{"_start_at":"2013-01-28T00:00:00+00:00","_end_at":"2013-02-04T00:00:00+00:00","_count":2}"
          and the "1st" result should have "values" with item "{"_start_at":"2013-02-04T00:00:00+00:00","_end_at":"2013-02-11T00:00:00+00:00","_count":5}"

    Scenario: for an authority get weekly data between two points in time
         when I go to "/licensing?filter_by=authorityUrlSlug:testport&start_at=2013-02-04T00:00:00%2B00:00&end_at=2013-03-29T00:00:00%2B00:00&period=week"
         then I should get back a status of "200"
          and the JSON should have "8" results
          and the "1st" result should be "{"_start_at":"2013-02-04T00:00:00+00:00","_end_at":"2013-02-11T00:00:00+00:00","_count":10}"
          and the "2nd" result should be "{"_start_at":"2013-02-11T00:00:00+00:00","_end_at":"2013-02-18T00:00:00+00:00","_count":0}"
          and the "3rd" result should be "{"_start_at":"2013-02-18T00:00:00+00:00","_end_at":"2013-02-25T00:00:00+00:00","_count":0}"
          and the "4th" result should be "{"_start_at":"2013-02-25T00:00:00+00:00","_end_at":"2013-03-04T00:00:00+00:00","_count":0}"
          and the "5th" result should be "{"_start_at":"2013-03-04T00:00:00+00:00","_end_at":"2013-03-11T00:00:00+00:00","_count":16}"
          and the "6th" result should be "{"_start_at":"2013-03-11T00:00:00+00:00","_end_at":"2013-03-18T00:00:00+00:00","_count":21}"
          and the "7th" result should be "{"_start_at":"2013-03-18T00:00:00+00:00","_end_at":"2013-03-25T00:00:00+00:00","_count":1}"
          and the "8th" result should be "{"_start_at":"2013-03-25T00:00:00+00:00","_end_at":"2013-04-01T00:00:00+00:00","_count":4}"


    Scenario: for an authority get licences between two points in time
         when I go to "/licensing?group_by=licenceUrlSlug&filter_by=authorityUrlSlug:testport&start_at=2013-01-28T00:00:00%2B00:00&end_at=2013-03-29T00:00:00%2B00:00&collect=authorityName&collect=licenceName"
         then I should get back a status of "200"
          and the JSON should have "6" results
          and the "1st" result should have "licenceUrlSlug" equaling "fake-licence-2"
          and the "1st" result should have "_count" equaling the integer "12"
          and the "1st" result should have "licenceName" with item ""Fake Licence 2""
          and the "2nd" result should have "licenceUrlSlug" equaling "fake-licence-5"
          and the "2nd" result should have "_count" equaling the integer "12"
          and the "2nd" result should have "licenceName" with item ""Fake Licence 5""


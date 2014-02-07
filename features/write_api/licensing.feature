@use_write_api_client
Feature: licensing -> performance platform integration

    Scenario: receiving data from licensing
        Given I have the data in "SubmittedApplicationsReport.json"
          and I have a bucket named "licensing"
          and I use the bearer token for the bucket
         when I post the data to "/licensing"
         then I should get back a status of "200"

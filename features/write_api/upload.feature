@use_splinter_client
Feature: csv upload

    Scenario: upload a csv file
       When I go to "/my_bucket/upload"
       then I should get back a status of "200"

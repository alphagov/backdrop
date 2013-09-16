@use_splinter_client
Feature: virus upload

    Scenario: Upload virus data
        Given I am logged in
        when I go to "/my_bucket/upload"
         and I enter "virus.csv" into the file upload field
         and I click "Upload"
        then I should see the virus error message

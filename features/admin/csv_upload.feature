@use_admin_client
Feature: CSV Upload

  Scenario: Upload CSV data
    Given I have a bucket named "my_bucket"
    And   bucket setting upload_format is "csv"
    And   admin I am logged in
    And   I can upload to "my_bucket"
    And   a file named "data.csv"
          """
          name,age,nationality
          Pawel,27,Polish
          Max,35,Italian
          """
    When  I go to "/my_bucket/upload"
    And   I enter "data.csv" into the file upload field
    And   I click "Upload"
    Then  the "my_bucket" bucket should contain in any order:
          """
          {"name": "Pawel", "age": "27", "nationality": "Polish"}
          {"name": "Max", "age": "35", "nationality": "Italian"}
          """

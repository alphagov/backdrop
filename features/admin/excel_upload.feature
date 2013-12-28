@use_admin_client
Feature: excel upload

  Scenario: Upload XLSX file
    Given a file named "data.xlsx" with fixture "data.xlsx"
    And   I have a bucket named "my_xlsx_bucket"
    And   bucket setting upload_format is "excel"
    And   admin I am logged in
    And   I can upload to "my_xlsx_bucket"
    When  I go to "/my_xlsx_bucket/upload"
    And   I enter "data.xlsx" into the file upload field
    And   I click "Upload"
    Then  the "my_xlsx_bucket" bucket should contain in any order
          """
          {"name": "Pawel", "age": 27, "nationality": "Polish"}
          {"name": "Max", "age": 35, "nationality": "Italian"}
          """

  Scenario: using _timestamp for an auto id
    Given a file named "LPA_MI_EXAMPLE.xls" with fixture "LPA_MI_EXAMPLE.xls"
    And   I have a bucket named "bucket_with_timestamp_auto_id"
    And   bucket setting upload_format is "excel"
    And   admin I am logged in
    And   I can upload to "bucket_with_timestamp_auto_id"
    When  I go to "/bucket_with_timestamp_auto_id/upload"
    And   I enter "LPA_MI_EXAMPLE.xls" into the file upload field
    And   I click "Upload"
    Then  the platform should have "18" items stored in "bucket_with_timestamp_auto_id"

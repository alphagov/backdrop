@use_admin_client
Feature: excel upload

  Scenario: Upload XLSX file
    Given a file named "data.xlsx" with fixture "data.xlsx"
    And   I have a data_set named "my_xlsx_data_set" with settings
        | key           | value   |
        | upload_format | "excel" |
    And   I am logged in
    And   I can upload to "my_xlsx_data_set"
    When  I go to "/my_xlsx_data_set/upload"
    And   I enter "data.xlsx" into the file upload field
    And   I click "Upload"
    Then  the "my_xlsx_data_set" data_set should contain in any order
          """
          {"name": "Pawel", "age": 27, "nationality": "Polish"}
          {"name": "Max", "age": 35, "nationality": "Italian"}
          """

  Scenario: using _timestamp for an auto id
    Given a file named "LPA_MI_EXAMPLE.xls" with fixture "LPA_MI_EXAMPLE.xls"
    And   I have a data_set named "data_set_with_timestamp_auto_id" with settings
        | key           | value   |
        | upload_format | "excel" |
    And   I am logged in
    And   I can upload to "data_set_with_timestamp_auto_id"
    When  I go to "/data_set_with_timestamp_auto_id/upload"
    And   I enter "LPA_MI_EXAMPLE.xls" into the file upload field
    And   I click "Upload"
    Then  the platform should have "18" items stored in "data_set_with_timestamp_auto_id"

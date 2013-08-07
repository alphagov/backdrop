@use_splinter_client
Feature: excel upload

    Scenario: Upload XLSX data
       Given a file named "data.xlsx" with fixture "data.xlsx"
         and I am logged in
        when I go to "/my_xlsx_bucket/upload"
         and I enter "data.xlsx" into the file upload field
         and I click "Upload"
        then the "my_xlsx_bucket" bucket should contain in any order:
             """
             {"name": "Pawel", "age": 27, "nationality": "Polish"}
             {"name": "Max", "age": 35, "nationality": "Italian"}
             """
    Scenario: using _timestamp for an auto id
       Given a file named "LPA_MI_EXAMPLE.xls" with fixture "LPA_MI_EXAMPLE.xls"
         and I am logged in
        when I go to "/bucket_with_timestamp_auto_id/upload"
         and I enter "LPA_MI_EXAMPLE.xls" into the file upload field
         and I click "Upload"
        then the platform should have "18" items stored in "bucket_with_timestamp_auto_id"

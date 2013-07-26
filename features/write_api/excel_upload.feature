@use_splinter_client
Feature: excel upload

    Scenario: Upload XLSX data
       Given a file named "data.xlsx" with fixture "data.xlsx"
         and I am logged in
        when I go to "/my_xlsx_bucket/upload"
         and I enter "data.xlsx" into the file upload field
         and I click "Upload"
        then the platform should have stored in "my_xlsx_bucket":
             """
             {"name": "Pawel", "age": 27, "nationality": "Polish"}
             {"name": "Max", "age": 35, "nationality": "Italian"}
             """
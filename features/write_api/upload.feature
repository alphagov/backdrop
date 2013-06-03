@use_splinter_client
Feature: csv upload

    Scenario: retrieve upload page
       Given a file named "data.csv":
             """
             name,age,nationality
             Pawel,27,Polish
             Max,35,Italian
             """
         and I am logged in
        when I go to "/my_bucket/upload"
         and I enter "data.csv" into the file upload field
         and I click "submit"
        then the platform should have stored in "my_bucket":
             """
             {"name": "Pawel", "age": "27", "nationality": "Polish"}
             {"name": "Max", "age": "35", "nationality": "Italian"}
             """

    Scenario: UTF8 characters
       Given a file named "data.csv":
             """
             english,italian
             city,città
             coffee,caffè
             """
         and I am logged in
        when I go to "/my_bucket/upload"
         and I enter "data.csv" into the file upload field
         and I click "submit"
        then the platform should have stored in "my_bucket":
             """
             {"english": "city", "italian": "città"}
             {"english": "coffee", "italian": "caffè"}
             """

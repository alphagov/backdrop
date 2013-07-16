@use_splinter_client
Feature: csv upload

    Scenario: Upload CSV data
       Given a file named "data.csv":
             """
             name,age,nationality
             Pawel,27,Polish
             Max,35,Italian
             """
         and I am logged in
        when I go to "/my_bucket/upload"
         and I enter "data.csv" into the file upload field
         and I click "Upload"
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
         and I click "Upload"
        then the platform should have stored in "my_bucket":
             """
             {"english": "city", "italian": "città"}
             {"english": "coffee", "italian": "caffè"}
             """

    # If the uploaded CSV does not have an _id column,
    # overwrite records with the same combination of:
    #    start_at, end_at and key
    @wip
    Scenario: Overwrite data with matching properties
       Given a file named "data.csv":
             """
             start_at,end_at,key,value
             2013-01-01,2013-01-07,abc,0
             2013-01-01,2013-01-07,def,0
             """
         and a file named "data2.csv":
             """
             start_at,end_at,key,value
             2013-01-01,2013-01-07,abc,287
             2013-01-01,2013-01-07,def,425
             """
         and I am logged in
        when I go to "/bucket_with_auto_id/upload"
         and I enter "data.csv" into the file upload field
         and I click "Upload"
         and I go to "/bucket_with_auto_id/upload"
         and I enter "data2.csv" into the file upload field
         and I click "Upload"
        then the platform should have stored in "bucket_with_auto_id":
             """
             {"start_at": "2013-01-01", "end_at": "2013-01-07", "key": "abc", "value": "287"}
             {"start_at": "2013-01-01", "end_at": "2013-01-07", "key": "def", "value": "425"}
             """

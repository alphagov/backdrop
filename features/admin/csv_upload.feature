@use_admin_client
Feature: CSV Upload

  Scenario: Upload CSV data
    Given I have a bucket named "my_bucket"
    And   bucket setting upload_format is "csv"
    And   I am logged in
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

  Scenario: UTF8 characters
    Given a file named "data.csv":
          """
          english,italian
          city,città
          coffee,caffè
          """
    And   I have a bucket named "my_bucket"
    And   bucket setting upload_format is "csv"
    And   I am logged in
    And   I can upload to "my_bucket"
    When  I go to "/my_bucket/upload"
    And   I enter "data.csv" into the file upload field
    And   I click "Upload"
    Then  the "my_bucket" bucket should contain in any order:
          """
          {"english": "city", "italian": "città"}
          {"english": "coffee", "italian": "caffè"}
          """

  # If the uploaded CSV does not have an _id column,
  # overwrite records with the same combination of:
  #    start_at, end_at and key
  # NB! this is a wip because selenium is buggy
  @wip
  Scenario: Overwrite data with matching properties
    Given a file named "data.csv":
          """
          start_at,end_at,key,value
          2013-01-01,2013-01-07,abc,0
          2013-01-01,2013-01-07,def,0
          """
    And   a file named "data2.csv":
          """
          start_at,end_at,key,value
          2013-01-01,2013-01-07,abc,287
          2013-01-01,2013-01-07,def,425
          """
    And   I have a bucket named "bucket_with_auto_id"
    And   bucket setting upload_format is "csv"
    And   I am logged in
    And   I can upload to "bucket_with_auto_id"
    When  I go to "/bucket_with_auto_id/upload"
    And   I enter "data.csv" into the file upload field
    And   I click "Upload"
    And   I go to "/bucket_with_auto_id/upload"
    And   I enter "data2.csv" into the file upload field
    And   I click "Upload"
    Then  the "bucket_with_auto_id" bucket should contain in any order:
          """
          {"start_at": "2013-01-01", "end_at": "2013-01-07", "key": "abc", "value": "287"}
          {"start_at": "2013-01-01", "end_at": "2013-01-07", "key": "def", "value": "425"}
          """

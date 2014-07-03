@use_admin_client
Feature: CSV Upload

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
    And   I have a data_set named "data_set_with_auto_id" with settings
        | key           | value |
        | upload_format | "csv" |
    And   I am logged in
    And   I can upload to "data_set_with_auto_id"
    When  I go to "/data_set_with_auto_id/upload"
    And   I enter "data.csv" into the file upload field
    And   I click "Upload"
    And   I go to "/data_set_with_auto_id/upload"
    And   I enter "data2.csv" into the file upload field
    And   I click "Upload"
    Then  the "data_set_with_auto_id" data_set should contain in any order:
          """
          {"start_at": "2013-01-01", "end_at": "2013-01-07", "key": "abc", "value": "287"}
          {"start_at": "2013-01-01", "end_at": "2013-01-07", "key": "def", "value": "425"}
          """

@use_admin_client
Feature: csv upload validation

  Scenario: more values than columns
    Given a file named "data.csv":
          """
          name,age,nationality
          Pawel,27,Polish,male
          Max,35,Italian,male
          """
    And   I have a data_set named "foo" with settings
        | key           | value |
        | upload_format | "csv" |
    And   I am logged in
    And   I can upload to "foo"
    When  I go to "/foo/upload"
    And   I enter "data.csv" into the file upload field
    And   I click "Upload"
    Then  I should see the text "There was an error with your upload"
    And   the platform should have "0" items stored in "foo"

  Scenario: missing values for some columns
    Given a file named "data.csv":
          """
          name,age,nationality,gender
          Pawel,27,Polish,male
          Max,35,Italian
          """
    And   I have a data_set named "foo" with settings
        | key           | value |
        | upload_format | "csv" |
    And   I am logged in
    And   I can upload to "foo"
    When  I go to "/foo/upload"
    And   I enter "data.csv" into the file upload field
    And   I click "Upload"
    Then  I should see the text "There was an error with your upload"
    And   the platform should have "0" items stored in "foo"

  Scenario: file too large
    Given a file named "data.csv" of size "1000000" bytes
    And   I have a data_set named "foo" with settings
        | key           | value |
        | upload_format | "csv" |
    And   I am logged in
    And   I can upload to "foo"
    When  I go to "/foo/upload"
    And   I enter "data.csv" into the file upload field
    And   I click "Upload"
    Then  I should see the text "There was an error with your upload"
    And   the platform should have "0" items stored in "foo"

  Scenario: non UTF8 characters
    Given a file named "data.csv" with fixture "bad-characters.csv"
    And   I have a data_set named "foo" with settings
        | key           | value |
        | upload_format | "csv" |
    And   I am logged in
    And   I can upload to "foo"
    When  I go to "/foo/upload"
    And   I enter "data.csv" into the file upload field
    And   I click "Upload"
    Then  I should see the text "There was an error with your upload"
    And   the platform should have "0" items stored in "foo"

  Scenario: no file is provided
    Given I am logged in
    And   I have a data_set named "foo"
    And   I can upload to "foo"
    When  I go to "/foo/upload"
    And   I click "Upload"
    Then  I should see the text "There was an error with your upload"
    And   the platform should have "0" items stored in "foo"

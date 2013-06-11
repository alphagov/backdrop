@use_splinter_client
Feature: csv upload validation

    Scenario: more values than columns
       Given a file named "data.csv":
             """
             name,age,nationality
             Pawel,27,Polish,male
             Max,35,Italian,male
             """
         and I am logged in
        when I go to "/foo/upload"
         and I enter "data.csv" into the file upload field
         and I click "submit"
        then I should see the text "There was an error with your upload"
         and the platform should have "0" items stored in "foo"

    Scenario: missing values for some columns
       Given a file named "data.csv":
             """
             name,age,nationality,gender
             Pawel,27,Polish,male
             Max,35,Italian
             """
         and I am logged in
        when I go to "/foo/upload"
         and I enter "data.csv" into the file upload field
         and I click "submit"
        then I should see the text "There was an error with your upload"
         and the platform should have "0" items stored in "foo"

    Scenario: file too large
       Given a file named "data.csv" of size "100000" bytes
         and I am logged in
        when I go to "/foo/upload"
         and I enter "data.csv" into the file upload field
         and I click "submit"
        then I should see the text "There was an error with your upload"
         and the platform should have "0" items stored in "foo"

    Scenario: non UTF8 characters
       Given a file named "data.csv" with fixture "bad-characters.csv"
         and I am logged in
        when I go to "/foo/upload"
         and I enter "data.csv" into the file upload field
         and I click "submit"
        then I should see the text "There was an error with your upload"
         and the platform should have "0" items stored in "foo"

    Scenario: no file is provided
       Given I am logged in
        when I go to "/foo/upload"
         and I click "submit"
        then I should see the text "There was an error with your upload"
         and the platform should have "0" items stored in "foo"
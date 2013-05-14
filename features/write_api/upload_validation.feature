@use_http_client
Feature: csv upload validation

    Scenario: more values than columns
       Given a file named "data.csv":
             """
             name,age,nationality
             Pawel,27,Polish,male
             Max,35,Italian,male
             """
        when I post the file "data.csv" to "/foo/upload"
        then I should get back a status of "400"

    Scenario: missing values for some columns
       Given a file named "data.csv":
             """
             name,age,nationality,gender
             Pawel,27,Polish,male
             Max,35,Italian
             """
        when I post the file "data.csv" to "/foo/upload"
        then I should get back a status of "400"
         and the platform should have "0" items stored in "foo"

    Scenario: file too large
       Given a file named "data.csv" of size "100000" bytes
        when I post the file "data.csv" to "/foo/upload"
        then I should get back a status of "411"

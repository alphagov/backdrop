Feature: licensing -> performance platform integration

    Scenario: receiving data from licensing
        Given I have the data in "SubmittedApplicationsReport.json"
         when I post the data to "/licensing"
         then I should get back a status of "200"

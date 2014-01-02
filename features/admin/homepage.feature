@use_admin_client
Feature: Homepage

  Scenario: Visit the home page
    When I go to "/"
    Then I should get back a status of "200"

  Scenario: Visit the /_user resource
    When I go to "/_user"
    Then I should get back a status of "301"

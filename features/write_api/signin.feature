@use_splinter_client
Feature: Sign in

    Scenario: Show signed-in user name
       Given I am logged in as "Max"
        when I go to "/_user"
        then I should see the text "Signed in as Max"

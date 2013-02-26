Feature: end-to-end platform test

    Scenario: write and retrieve data from platform
        Given I have the data in "dinosaurs.json"
         when I post the data to "/reptiles"
          and I go to "/reptiles?filter_by=size:big"
         then I should get back a status of "200"
          and the JSON should have "2" result(s)

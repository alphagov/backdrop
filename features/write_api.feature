Feature: the performance platform write api

    Scenario: hitting the health check url
         When I go to "/_status"
         then I should get back a status of "200"

    Scenario: posting to a reserved bucket name
        Given I have the data in "dinosaur.json"
         when I post the data to "/_bucket"
         then I should get back a status of "400"

    Scenario: posting one object to a bucket
        Given I have the data in "dinosaur.json"
         when I post the data to "/my_dinosaur_bucket"
         then I should get back a status of "200"
         and  the stored data should contain "1" "name" equaling "t-rex"

    Scenario: posting a list of objects to a bucket
        Given I have the data in "dinosaurs.json"
         when I post the data to "/my_dinosaur_bucket"
         then I should get back a status of "200"
         and  the stored data should contain "2" "size" equaling "big"
         and  the stored data should contain "1" "name" equaling "microraptor"

@use_read_api_client
Feature: collect fields into grouped responses


    Scenario: should be able to collect on a key for grouped queries
         Given "licensing_2.json" is in "foo" data_set
          when I go to "/foo?collect=authority&group_by=licence_name"
          then I should get back a status of "200"
          and the "1st" result should have "authority" with item ""Westminster""
          and the "2nd" result should have "authority" with item ""Westminster""
          and the "2nd" result should have "authority" with item ""Camden""


    Scenario: should be able to collect on a key for period grouped queries
         Given "licensing_2.json" is in "foo" data_set
          when I go to "/foo?collect=authority&period=week&group_by=licence_name&start_at=2012-12-03T00:00:00Z&end_at=2012-12-17T00:00:00Z"
          then I should get back a status of "200"
          and the "2nd" result should have "authority" with item ""Westminster""
          and the "2nd" result should have "authority" with item ""Camden""


    Scenario: should not be able to collect on non grouped queries
         Given "licensing_2.json" is in "foo" data_set
          when I go to "/foo?collect=authority"
          then I should get back a status of "400"


    Scenario: should be able to collect false values
        Given "licensing_2.json" is in "foo" data_set
         when I go to "/foo?group_by=licence_name&filter_by=isPaymentRequired:false&collect=isPaymentRequired"
         then I should get back a status of "200"
         and the "1st" result should have "isPaymentRequired" with item "false"

    Scenario: should be able to perform maths on collect
        Given "sort_and_limit.json" is in "foo" data_set
         when I go to "/foo?group_by=type&filter_by=type:wild&collect=value:sum&collect=value:mean"
         then I should get back a status of "200"
         and the "1st" result should have "value:sum" with json "27"
         and the "1st" result should have "value:mean" with json "6.75"

    Scenario: should be able to perform maths on sub groups
        Given "evl_volumetrics.json" is in "foo" data_set
         when I go to "/foo?period=month&group_by=channel&collect=volume:sum&start_at=2012-04-01T00:00:00Z&end_at=2012-05-01T00:00:00Z"
         then I should get back a status of "200"
         and the "1st" result should have "volume:sum" with json "1862526.0"
         and the "1st" result should have a sub group with "volume:sum" with json "1862526.0"

    Scenario: should receive a nice error when performing invalid operation
        Given "dinosaurs.json" is in "foo" data_set
         when I go to "/foo?group_by=type&collect=name:sum"
         then I should get back a status of "400"


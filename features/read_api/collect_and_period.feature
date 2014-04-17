@use_read_api_client
Feature: combining period and group queries

  Background:
      Given "collectables.json" is in "collect_me" data_set

  Scenario: combining a period and collect query
    when I go to "/collect_me?period=week&collect=pickup&start_at=2013-08-05T00:00:00Z&end_at=2013-08-12T00:00:00Z"
    then I should get back a status of "200"
     and the JSON should have "1" result(s)
     and the "1st" result should be "{"_count": 2.0, "pickup:set": ["mushroom", "ring"], "_end_at": "2013-08-12T00:00:00+00:00", "pickup": ["mushroom", "ring"], "_start_at": "2013-08-05T00:00:00+00:00"}"

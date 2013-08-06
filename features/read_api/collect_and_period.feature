@use_read_api_client
Feature: combining period and group queries

  Background:
      Given "collectables.json" is in "collect_me" bucket

  Scenario: combining a period and collect query
    when I go to "/collect_me?period=week&collect=pickup"
    then I should get back a status of "200"
    and the "1st" result should be "{"foo": "bar"}"

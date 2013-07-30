@use_splinter_client
Feature: EVL Upload

    @wip
    Scenario: Upload call center volumes
       Given a file named "CEG Data.xlsx" with fixture "contrib/CEG Transaction Tracker.xlsx"
         and I am logged in
        when I go to "/evl_ceg_data/upload"
         and I enter "CEG Data.xlsx" into the file upload field
         and I click "Upload"
        then the platform should have "14" items stored in "evl_ceg_data"
         and the platform should have stored in "evl_ceg_data":
             """
             {"_timestamp": "2012-04-01T00:00:00+00:00", "timeSpan":"month", "relicensing_web": 1551564, "relicensing_ivr": 251634, "relicensing_agent": 7159, "sorn_web": 207689, "sorn_ivr": 48313, "sorn_agent": 48313, "agent_automated_dupes": 7489, "calls_answered_by_advisor": 32214}
             {"_timestamp": "2013-02-01T00:00:00+00:00", "timeSpan":"month", "relicensing_web": 1861016, "relicensing_ivr": 300243, "relicensing_agent": 9225, "sorn_web": 208062, "sorn_ivr": 41724, "sorn_agent": 3434, "agent_automated_dupes": 6833, "calls_answered_by_advisor": 30437}
             """

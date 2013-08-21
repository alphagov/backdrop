@use_splinter_client
Feature: EVL Upload

    Scenario: Upload call center volumes
       Given a file named "CEG Data.xlsx" with fixture "contrib/CEG Transaction Tracker.xlsx"
         and I am logged in
        when I go to "/evl_ceg_data/upload"
         and I enter "CEG Data.xlsx" into the file upload field
         and I click "Upload"
        then the platform should have "71" items stored in "evl_ceg_data"
         and the "evl_ceg_data" bucket should have items:
             """
             {"_timestamp": "2008-09-01T00:00:00+00:00", "_id": "2008-09-01", "timeSpan":"month", "relicensing_web": 1039833, "relicensing_ivr": 249488, "relicensing_agent": 7935, "sorn_web": 161110, "sorn_ivr": 49889, "sorn_agent": 1345, "agent_automated_dupes": 13723, "calls_answered_by_advisor": 63575}
             {"_timestamp": "2012-04-01T00:00:00+00:00", "_id": "2012-04-01", "timeSpan":"month", "relicensing_web": 1551564, "relicensing_ivr": 251634, "relicensing_agent": 7159, "sorn_web": 207689, "sorn_ivr": 48313, "sorn_agent": 2141, "agent_automated_dupes": 7489, "calls_answered_by_advisor": 32214}
             {"_timestamp": "2013-02-01T00:00:00+00:00", "_id": "2013-02-01", "timeSpan":"month", "relicensing_web": 1861016, "relicensing_ivr": 300243, "relicensing_agent": 9225, "sorn_web": 208062, "sorn_ivr": 41724, "sorn_agent": 3434, "agent_automated_dupes": 6833, "calls_answered_by_advisor": 30437}
             """

    Scenario: Upload services volumetrics
       Given a file named "EVL Volumetrics.xlsx" with fixture "contrib/EVL Services Volumetrics Sample.xls"
         and I am logged in
        when I go to "/evl_services_volumetrics/upload"
         and I enter "EVL Volumetrics.xlsx" into the file upload field
         and I click "Upload"
        then the platform should have "1" items stored in "evl_services_volumetrics"
         and the "evl_services_volumetrics" bucket should have items:
             """
             {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01", "timeSpan":"day", "successful_tax_disc": 151065, "successful_sorn": 16718}
             """

    Scenario: Upload service failures
        Given a file named "EVL Volumetrics.xlsx" with fixture "contrib/EVL Services Volumetrics Sample.xls"
         and I am logged in
        when I go to "/evl_services_failures/upload"
         and I enter "EVL Volumetrics.xlsx" into the file upload field
         and I click "Upload"
        then the platform should have "136" items stored in "evl_services_failures"
         and the "evl_services_failures" bucket should have items:
             """
             {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01.tax-disc.0", "type": "tax-disc", "reason": 0, "count": 89, "description": "Abandoned"}
             {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01.tax-disc.66", "type": "tax-disc", "reason": 66, "count": 50, "description": "LPB Response Code was PSP Session Timeout"}
             {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01.sorn.5", "type": "sorn", "reason": 5, "count": 354, "description": "User Cancelled Transaction"}
             """

    Scenario: Upload channel volumetrics
        Given a file named "EVL Volumetrics.xlsx" with fixture "contrib/EVL Channel Volumetrics Sample.xls"
         and I am logged in
        when I go to "/evl_channel_volumetrics/upload"
         and I enter "EVL Volumetrics.xlsx" into the file upload field
         and I click "Upload"
        then the platform should have "2" items stored in "evl_channel_volumetrics"
         and the "evl_channel_volumetrics" bucket should have items:
             """
             {"_timestamp": "2013-07-29T00:00:00+00:00", "_id": "2013-07-29", "successful_agent": 1039, "successful_ivr": 19985, "successful_web": 102182}
             {"_timestamp": "2013-07-30T00:00:00+00:00", "_id": "2013-07-30", "successful_agent": 1047, "successful_ivr": 18315, "successful_web": 100800}
             """

    Scenario: Upload customer satisfaction
        Given a file named "EVL Satisfaction.xlsx" with fixture "contrib/EVL Customer Satisfaction.xlsx"
         and I am logged in
        when I go to "/evl_customer_satisfaction/upload"
         and I enter "EVL Satisfaction.xlsx" into the file upload field
         and I click "Upload"
        then the platform should have "113" items stored in "evl_customer_satisfaction"
         and the "evl_customer_satisfaction" bucket should have items:
             """
             {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01", "satisfaction_tax_disc": 0.425385001089928, "satisfaction_sorn": 0.762844168796153}
             {"_timestamp": "2007-07-01T00:00:00+00:00", "_id": "2007-07-01", "satisfaction_tax_disc": 0.372564254686694, "satisfaction_sorn": 0.473557589451075}
             """

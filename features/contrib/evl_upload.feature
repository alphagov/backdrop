@use_admin_client
Feature: EVL Upload

    Scenario: Upload call center volumes
       Given a file named "CEG Data.xlsx" with fixture "contrib/CEG Transaction Tracker.xlsx"
         and I have a bucket named "evl_ceg_data" with settings
            | key            | value                                                                                                 |
            | upload_format  | "excel"                                                                                               |
            | upload_filters | ["backdrop.core.upload.filters.first_sheet_filter","backdrop.contrib.evl_upload_filters.ceg_volumes"] |
         and I am logged in
         and I can upload to "evl_ceg_data"
        when I go to "/evl_ceg_data/upload"
         and I enter "CEG Data.xlsx" into the file upload field
         and I click "Upload"
        then the platform should have "71" items stored in "evl_ceg_data"
         and the "evl_ceg_data" bucket should have items:
             """
             {"_timestamp": "2008-09-01T00:00:00+00:00", "_id": "2008-09-01", "timeSpan":"month", "relicensing_web": 100, "relicensing_ivr": 200, "relicensing_agent": 700, "sorn_web": 1100, "sorn_ivr": 1200, "sorn_agent": 1300, "agent_automated_dupes": 1400, "calls_answered_by_advisor": 1500}
             """

    Scenario: Upload services volumetrics
       Given a file named "EVL Volumetrics.xlsx" with fixture "contrib/EVL Services Volumetrics Sample.xls"
         and I have a bucket named "evl_services_volumetrics" with settings
            | key            | value                                                                                                         |
            | upload_format  | "excel"                                                                                                       |
            | upload_filters | ["backdrop.core.upload.filters.first_sheet_filter","backdrop.contrib.evl_upload_filters.service_volumetrics"] |
         and I am logged in
         and I can upload to "evl_services_volumetrics"
        when I go to "/evl_services_volumetrics/upload"
         and I enter "EVL Volumetrics.xlsx" into the file upload field
         and I click "Upload"
        then the platform should have "1" items stored in "evl_services_volumetrics"
         and the "evl_services_volumetrics" bucket should have items:
             """
             {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01", "timeSpan":"day", "successful_tax_disc": 100.0, "successful_sorn": 200.0}
             """

    Scenario: Upload service failures
        Given a file named "EVL Volumetrics.xlsx" with fixture "contrib/EVL Services Volumetrics Sample.xls"
         and I have a bucket named "evl_services_failures" with settings
            | key            | value                                                    |
            | upload_format  | "excel"                                                  |
            | upload_filters | ["backdrop.contrib.evl_upload_filters.service_failures"] |
         and I am logged in
         and I can upload to "evl_services_failures"
        when I go to "/evl_services_failures/upload"
         and I enter "EVL Volumetrics.xlsx" into the file upload field
         and I click "Upload"
        then the platform should have "136" items stored in "evl_services_failures"
         and the "evl_services_failures" bucket should have items:
             """
             {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01.tax-disc.0", "type": "tax-disc", "reason": 0, "count": 1, "description": "Abandoned"}
             {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01.tax-disc.66", "type": "tax-disc", "reason": 66, "count": 67, "description": "LPB Response Code was PSP Session Timeout"}
             {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01.sorn.5", "type": "sorn", "reason": 5, "count": 8, "description": "User Cancelled Transaction"}
             """

    Scenario: Upload channel volumetrics
        Given a file named "EVL Volumetrics.xlsx" with fixture "contrib/EVL Channel Volumetrics Sample.xls"
         and I have a bucket named "evl_channel_volumetrics" with settings
            | key            | value                                                                                                         |
            | upload_format  | "excel"                                                                                                       |
            | upload_filters | ["backdrop.core.upload.filters.first_sheet_filter","backdrop.contrib.evl_upload_filters.channel_volumetrics"] |
         and I am logged in
         and I can upload to "evl_channel_volumetrics"
        when I go to "/evl_channel_volumetrics/upload"
         and I enter "EVL Volumetrics.xlsx" into the file upload field
         and I click "Upload"
        then the platform should have "2" items stored in "evl_channel_volumetrics"
         and the "evl_channel_volumetrics" bucket should have items:
             """
             {"_timestamp": "2013-07-29T00:00:00+00:00", "_id": "2013-07-29", "successful_agent": 100.0, "successful_ivr": 101.0, "successful_web": 102.0, "total_agent": 200.0, "total_ivr": 201.0, "total_web": 202.0}
             {"_timestamp": "2013-07-30T00:00:00+00:00", "_id": "2013-07-30", "successful_agent": 101.0, "successful_ivr": 102.0, "successful_web": 103.0, "total_agent": 201.0, "total_ivr": 202.0, "total_web": 203.0}
             """

    Scenario: Upload customer satisfaction
        Given a file named "EVL Satisfaction.xlsx" with fixture "contrib/EVL Customer Satisfaction.xlsx"
         and I have a bucket named "evl_customer_satisfaction" with settings
            | key            | value                                                                                                           |
            | upload_format  | "excel"                                                                                                         |
            | upload_filters | ["backdrop.core.upload.filters.first_sheet_filter","backdrop.contrib.evl_upload_filters.customer_satisfaction"] |
         and I am logged in
         and I can upload to "evl_customer_satisfaction"
        when I go to "/evl_customer_satisfaction/upload"
         and I enter "EVL Satisfaction.xlsx" into the file upload field
         and I click "Upload"
        then the platform should have "113" items stored in "evl_customer_satisfaction"
         and the "evl_customer_satisfaction" bucket should have items:
             """
             {"_timestamp": "2013-08-01T00:00:00+00:00", "_id": "2013-08-01", "satisfaction_tax_disc": 1.2487024060928635, "satisfaction_sorn": 1.4370298628996634}
             {"_timestamp": "2007-07-01T00:00:00+00:00", "_id": "2007-07-01", "satisfaction_tax_disc": 1.1662755514934828, "satisfaction_sorn": 1.3581011781786714}
             """

    Scenario: Upload evl volumetrics
        Given a file named "evl-volumetrics.xls" with fixture "contrib/evl-volumetrics.xls"
         and I have a bucket named "evl_volumetrics" with settings
            | key            | value                                               |
            | upload_format  | "excel"                                             |
            | upload_filters | ["backdrop.contrib.evl_upload_filters.volumetrics"] |
         and I am logged in
         and I can upload to "evl_volumetrics"
        when I go to "/evl_volumetrics/upload"
         and I enter "evl-volumetrics.xls" into the file upload field
         and I click "Upload"
        then the platform should have "336" items stored in "evl_volumetrics"
         and the "evl_volumetrics" bucket should have items:
             """
             {"_timestamp": "2012-04-01T00:00:00+00:00", "transaction": "V-V890 SORN Declaration Refunds Input", "service": "sorn", "volume": 1025.0}
             {"_timestamp": "2012-05-01T00:00:00+00:00", "transaction": "V-V890 SORN Declaration Vehicles Input", "service": "sorn", "volume": 0.0}
             {"_timestamp": "2012-06-01T00:00:00+00:00", "transaction": "V-V890 SORN Declaration Vehicles Triage", "service": "sorn", "volume": 0.0}
             """

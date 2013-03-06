python licensing_location_data.py | mongoimport --db backdrop --collection licensing --upsertFields licence,authority,interaction,location,start_at,end_at --jsonArray

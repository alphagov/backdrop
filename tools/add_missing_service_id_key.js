/*
    From the backdrop repository, run:
    mongo tools/add_missing_service_id_key.js
*/

conn = new Mongo();
db = conn.getDB("backdrop");
var count = 0;


db.service_aggregates_latest_dataset_values.find().forEach(function(data) {
    if (!('service_id' in data)) {
        printjson(data);
        db.service_aggregates_latest_dataset_values.update(
             { "_id" : data["_id"] },
             { "$set" : { "service_id" : data["dashboard_slug"] } }
        );
        count+=1;
    }
})

printjson(count);

/*
    From the backdrop repository, run:
    mongo tools/delete_empty_summary_records.js
*/

conn = new Mongo();
db = conn.getDB("backdrop");

printjson({"Record count before remove": db.transactional_services_summaries.count()})

db.transactional_services_summaries.remove({"service_id": ""})

printjson({"Record count after remove": db.transactional_services_summaries.count()})

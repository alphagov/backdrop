# ADR 2: Persistent storage

# Context

The way the Government Digital Service (GDS) [makes technology choices is
described in the service manual](https://www.gov.uk/service-manual/making-software/choosing-technology). We are selecting which technology will to use to provide
persistence for the Performance Platform.

GDS has experience in running MongoDB and MySQL in production.

We envisage the Performance Platform as taking in unstructured data from a
variety of data sources (spreadsheets, analytics, logs, other databases and
applications) and allowing people to collect this data in a single place. This
should enable service managers to:

- make comparisons
- see how well their service is performing
- see how the performance changes over time, as they iterate the service

So we want a persistent data store that will store unstructured data, and
allow us to apply a structure either by post-processing the data, or at query
time.

The volume of the data that we are envisaging at this stage is pretty small.
We will be building a small thing to start; as we learn more about the
user needs and problem space, then we will revisit this decision. Since the
volume is small, it does not seem likely that we need Hadoop / HDFS or
Cassandra.

We are not the canonical source of this data. We are an aggregator; the
canonical source remains the data sources which will be providing feeds or
pushing the data into the Performance Platform.

Because of this position, we do not need ACID properties for this data, nor
need worry about the CAP theorem in any detail.

# Decision

We will use MongoDB. We are comfortable operating it in production,
it will allow unstructured data (in the form of JSON documents) and we can
apply structure at query time.

# Status

Accepted.

# Consequences

Use MongoDB with an appropriate replica-set configuration.

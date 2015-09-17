# ADR 1: Implementation Language

# Context

The way the Government Digital Service (GDS) [makes technology choices is
described in the service manual](https://www.gov.uk/service-manual/making-software/choosing-technology). We are selecting which language to write the data
API for the Performance Platform.

GDS has experience in running Ruby (Rails/Sinatra) and Scala apps in
production. Choosing one of these (Ruby) would allow us to rotate people
across GDS in and out of the Performance Platform team.

But we have some excellent Python developers in GDS, who
develop in Ruby at work. There is a community here that we expect would be
interested in working in their preferred language, so choosing Python
might be an way of encouraging rotation (people would not have to leave
the organisation to try a new thing) and diversity.

We have:

- lots of people here that have operated Python applications in
  production
- knowledge about how to architect and write Python applications
- an easy step to deploying Python in production

# Decision

We will write the data API in Python.

# Status

Accepted.

# Consequences

We will have to write (Capistrano or Fabric?) code to deploy a Python
application.


# ADR 3: Web Framework

# Context

The way the Government Digital Service (GDS) [makes technology choices is
described in the service manual](https://www.gov.uk/service-manual/making-software/choosing-technology). We are selecting which web framework to use for the data
API for the Performance Platform.

We are writing the API in Python. We need to support accepting unstructured
data, and returning structured data for reads.

The API will not be RESTful initially. We want to optimise for easy writing,
and do the hard work to return structured data at read time. We do not
understand the model or resources that we will be using, so for now, we think
we will allow data sets to be created and written to, and do some
transformations at query time on those data sets.

This means that we think we need to allow simple POST/PUT to a data set, and
then a more complex read query to produce structured data.

Over time, we expect to see common data sets / types and we can then look to
use a more structured approach, defining resources and relationships. At that
point, we might also want to consider using RESTful features, or switching
to a framework that has more support for that approach.

Options considered include Django and Flask, since we are familar with those.

# Decision

We will write the data API using Flask.

We don't need the ORM for Django, and Flask seems simpler in terms of starting
with a small API.

# Status

Accepted.

# Consequences

Devs and operations need to be comfortable with Flask apps.

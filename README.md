# Backdrop

[![Build Status](https://travis-ci.org/alphagov/backdrop.png?branch=master)](https://travis-ci.org/alphagov/backdrop?branch=master)

[![Dependency Status](https://gemnasium.com/alphagov/backdrop.png)](https://gemnasium.com/alphagov/backdrop)

[![Code Health](https://landscape.io/github/alphagov/backdrop/master/landscape.png)](https://landscape.io/github/alphagov/backdrop/master)

## What is it?

Backdrop is a datastore built with Python and MongoDB. It is made up of two separately deployable APIs for reading and writing data over HTTP. The plan is to be able to gather data from a variety of sources and then aggregate and compare this data in useful ways.

- Data is grouped into data sets.
- Data is stored by posting JSON to the write API.
- Certain types of data are identified by reserved keys eg events are objects containing a timestamp.
- Reserved keys start with an underscore eg `{ "_timestamp": "2013-01-01T00:00:00Z }"`
- Data is retrieved using HTTP GET requests against the read API.
- Data can be manipulated in a few useful ways with HTTP query strings eg `/$DATA_GROUP/$DATA_TYPE?period=month` for monthly grouped data.
- Backdrop is in constant development, so the best place to find examples and features are [the feature tests](https://github.com/alphagov/backdrop/tree/master/features)

## Getting set up

This assumes you are using the [Performance Platform development environment][pp-puppet] and so have Python and MongoDB installed.

1. Check that you have virtualenv installed, if not ```sudo apt-get install python-virtualenv```.
2. If you don't have virtualenvwrapper installed, create a virtualenv using ```virtualenv venv``` and ```source venv/bin/activate``` to enable it.
3. Navigate to the top level backdrop directory and run ```./run_tests.sh```.
This will create a new virtualenv (if virtualenvwraper is installed), install all dependencies and run the tests.
4. ```source venv/bin/activate``` to enable the virtualenv if you didn't do this in step 2.
5. Copy `backdrop/write/config/development_environment_sample.py` to `development_environment.py`
(if you want to) and edit as needed.

[pp-puppet]: https://github.com/alphagov/pp-puppet

### Starting the app

1. `./run_development.sh` will start backdrop read and write on ports 3038 and 3039 respectively
2. Confirm you're up and running by requesting http://www.development.performance.service.gov.uk/_status

To start just the read or write applications:

1. `./start-app.sh` takes two arguments: app (read or write) and port
2. `./start-app.sh read 3038` and/or  `./start-app.sh write 3039`

## Testing

Run tests with ```./run_tests.sh```

Splinter tests are not run in Travis or Jenkins due to their instability.

## Requesting data

Requests return a JSON object containing a `data` array.

`GET /data/$DATA_GROUP/$DATA_TYPE` will return an array of data. Each element is an object.

`GET /data/$DATA_GROUP/$DATA_TYPE?collect=score&group_by=name` will return an array. In this
case, each element of the array is an object containing a `name` value, a
`score` array with the scores for that name and a `_count` value with the
number of scores.

`GET /data/$DATA_GROUP/$DATA_TYPE?filter_by=name:Foo` returns all elements with `name` equal to "Foo".

`GET /data/$DATA_GROUP/$DATA_TYPE?filter_by_prefix=name:Foo` returns all elements with `name` beginning with "Foo".

Other parameters:

- `start_at` (YYYY-MM-DDTHH:MM:SS+HH:MM) and `end_at` (YYYY-MM-DDTHH:MM:SS+HH:MM)
- `period` ("week", "month")
- `sort_by` (`FIELD:ascending`)
- `limit` (integer)

## Useful tools

### Sync data from environment

Copy data from an environment to the local Backdrop database (should be run on your host machine): `bash tools/replicate-db.sh performance-mongo-1.integration`

You may need to setup your [ssh config](https://github.gds/pages/gds/opsmanual/2nd-line/technical-setup.html#ssh-config) correctly for this to work

To sync to the govuk dev vm, you can pass `govuk_dev` as the 2nd argument to this script -

`bash tools/replicate-db.sh performance-mongo-1.integration govuk_dev`


## Emptying a dataset

To empty a dataset, get its token from stagecraft. Then run the following curl
command

```
curl -X PUT -d "[]" https://{backdrop_url}/data/<data-group>/<data-type> -H 'Authorization: Bearer <token-from-stagecraft>' -H 'Content-Type: application/json'
```

## Transformers

Transformers run as part of the `backdrop-transformer-procfile-worker` service.

```
sudo service backdrop-transformer-procfile-worker status
```

## Triggering a transform manually

A transform occurs when data is written to in Backdrop. The transform applies
calculations to the data and writes the results to a second dataset.

You may wish to trigger a transform manually if data is missing from a output
data set.

Tranforms are configured in [Stagecraft][] via the API or Django admin
application.

[Stagecraft]: https://github.com/alphagov/stagecraft

1. Log in to the Stagecraft Django admin application to obtain a bearer token
   for the source data set:

    a. Select 'Data sets' from the 'Datasets' section in the main menu.
    b. Search for the source data set
    c. Make a note of the data group and data type for the data set you wish to
      transform
    d. Click on the name of the data set
    e. Copy the bearer token from the form field

1. Run the following command, replacing the fields in capitals:

   ```
   curl -H 'Authorization: Bearer <INSERT BEARER TOKEN HERE>' -H 'content-type: application/json' -d '{"_start_at": "2012-01-01T00:00:00Z", "_end_at": "2015-03-20T00:00:00Z"}' https://www.performance.service.gov.uk/data/<DATA GROUP>/<DATA TYPE>/transform
   ```

## Celery worker

Backdrop uses celery for running tasks on data post write - these can be found
in `backdrop/transformers/tasks/`

To process these tasks, you must run the worker - this can be done with the
following command

`celery worker -A backdrop.transformers.worker -l debug`


## Troubleshooting

The logs for RabbitMQ can be found in: `/var/log/rabbitmq/`
If there are any problems running transforms, this should be the first place to look.




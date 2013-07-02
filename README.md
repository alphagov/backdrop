# Backdrop

[![Build Status](https://travis-ci.org/alphagov/backdrop.png?branch=master)](https://travis-ci.org/alphagov/backdrop?branch=master)

##What is it?

Backdrop is a datastore built with python and mongo db. It is made up of two separately deployable APIs for reading and writing data over http. The plan is to be able to gather data from a variety of sources and then aggregate and compare this data in useful ways.

- Data is grouped into buckets.
- Data is stored by posting json to the write api.
- Certain types of data are identified by reserved keys. ie events are objects containing a timestamp.
- Reserved keys start with an underscore. eg `{ "_timestamp": "2013-01-01T00:00:00Z }"`
- Data is retrieved using http query strings on the read api.
- Data can be retrieved in a few useful ways. eg `/<name_of_my_bucket>?period=month` for monthly grouped data.
- Backdrop is in constant development, the best place to find examples and features are the feature tests https://github.com/alphagov/backdrop/tree/master/features

##Getting set up

This assumes you are using the GDS dev environment and so have python and mongo installed.

0. Check that you have virtualenv installed, if not ```sudo apt-get install python-virtualenv```.
1. Navigate to the ```performance-platform``` directory and run ```./run_tests.sh```. This will
create a new virtualenv, install all dependencies and run the tests.
2. ```source venv/bin/activate``` to enable the virtualenv.
3. Copy `backdrop/write/config/development_environment_sample.py` to `development_environment.py`
(if you want to) and edit as needed.

##Testing single sign on integration on dev

- Clone the signonotron2 project https://github.com/alphagov/signonotron2
- Use the rake tasks (`bundle exec rake -T` to list them) in order to create:
    - A new application **copy the generated client id and secret into `backdrop/write/config/development.py`**
    - Users with and without permissions to sign in to backdrop
- Start backdrop_write and signon
- Visit `www.dev.gov.uk:3039/_user/sign_in`

##Oauth Flow

This is the oauth flow we are using to authenticate users with Signonotron2

1. **GET** `/_user/sign_in` redirects user to signonotron2 asking them to give backdrop permission to see their data
2. User signs in allowing backdrop to see their data
3. **GET** (redirected from signonotron) `/_user/authorized?code=blahblahblah` 
    - **POST** (to signonotron) `/oauth/token` exchanges authorization code for access token so backdrop can query users data
    - **GET** (to signonotron) `/user.json` uses access token to get user data and see if they have permissions to sign in to backdrop
4. User is now signed in

## Requesting data

Requests return a JSON object containing a `data` array.

`GET /bucket_name` will return an array of data. Each element is an object.

`GET /bucket_name?collect=score&group_by=name` will return an array. In this
case, each element of the array is an object containing a `name` value, a
`score` array with the scores for that name and a `_count` value with the
number of scores.

`GET /bucket_name?filter_by=name:Foo` returns all elements with `name` equal to "Foo".

Other parameters:

- `start_at` (YYYY-MM-DDTHH:MM:SS+HH:MM) and `end_at` (YYYY-MM-DDTHH:MM:SS+HH:MM)
- `period` ("week", "month")
- `sort_by` (field)
- `limit` (number)
